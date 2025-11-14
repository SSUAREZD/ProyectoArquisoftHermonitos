#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

# --- Basic packages ---
apt-get update
apt-get install -y python3 python3-venv python3-pip git build-essential libpq-dev postgresql-client

APP_HOME=/opt/arquisoft
mkdir -p "$APP_HOME"
cd "$APP_HOME"

# --- Clone the main branch  ---
if [ ! -d "ProyectoArquisoftHermonitos" ]; then
  git clone --branch "${branch}" --single-branch "${repo_url}"
fi
cd ProyectoArquisoftHermonitos

# --- Python venv + deps ---
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
fi
pip install "psycopg2-binary>=2.9" gunicorn Pillow

# --- Django settings override (project folder is 'proyectoArquisoft') ---
SETTINGS_DIR="proyectoArquisoft"
SETTINGS_MAIN="$SETTINGS_DIR/settings.py"
SETTINGS_LOCAL="$SETTINGS_DIR/settings_local.py"

# Make settings.py import settings_local if not already present
grep -q "settings_local" "$SETTINGS_MAIN" || cat >> "$SETTINGS_MAIN" <<'PYEOF'

# --- auto-included by bootstrap ---
try:
    from .settings_local import *  # noqa
except Exception:
    pass
# --- end auto-included ---
PYEOF

# Write Postgres connection + allowed hosts
cat > "$SETTINGS_LOCAL" <<PYEOF
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "${db_name}",
        "USER": "${db_user}",
        "PASSWORD": "${db_password}",
        "HOST": "${db_host}",
        "PORT": "${db_port}",
        "CONN_MAX_AGE": 60,
    }
}
COGNITO_REGION = "us-east-1"
COGNITO_USER_POOL_ID = "us-east-1_tPnCimwiB"
COGNITO_APP_CLIENT_ID = "593e5kv7f4fm12vmpldkfbe8se"
PYEOF

# --- Wait for the creation of the database ---
echo "Waiting for DB to accept connections..."
for i in {1..30}; do
  if psql "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/postgres" -c "SELECT 1" >/dev/null 2>&1; then
    break
  fi
  sleep 4
done

psql "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/postgres" -c "CREATE DATABASE ${db_name};" || true

# --- Migrate ---
if [ -f manage.py ]; then
  DJANGO_DIR="."
else
  DJANGO_DIR="$(git rev-parse --show-toplevel)"
fi
cd "$DJANGO_DIR"
. .venv/bin/activate
python3 manage.py migrate --noinput || (sleep 5 && python3 manage.py migrate --noinput)

# --- small population (idempotente) ---
psql "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/${db_name}" -v ON_ERROR_STOP=1 <<'EOF' || true
-- Bodega (solo si no existe la de código BOD-001)
INSERT INTO core_bodega (codigo, nombre, ciudad, direccion, capacidad, longitud, latitud)
SELECT 'BOD-001', 'Bodega Central', 'Bogotá', 'Cra 7 # 72-41', 1000.00, -74.060, 4.664
WHERE NOT EXISTS (
  SELECT 1 FROM core_bodega WHERE codigo = 'BOD-001'
);

-- Ubicación (referenciando la bodega por código; evita duplicado por código de ubicación)
INSERT INTO core_ubicacion (codigo, tipo, capacidad_max, dimensiones, estado, bodega_id)
SELECT 'UB-01', 'Estanteria', 200.0, '2mx1mx1m', 'Disponible',
       (SELECT id FROM core_bodega WHERE codigo = 'BOD-001')
WHERE NOT EXISTS (
  SELECT 1 FROM core_ubicacion WHERE codigo = 'UB-01'
);

-- Productos (evita repetir por código/código de barras)
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7701234567890', 'Electronico', 1.5, 0.002, 'PRD-001'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-001' OR codigo_barras = '7701234567890'
);

INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7700987654321', 'Juguete', 0.3, 0.0005, 'PRD-002'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-002' OR codigo_barras = '7700987654321'
);

-- Inventario (inserta solo si no hay registro producto+bodega)
-- PRD-001 en BOD-001
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 50, 5, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-001'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );

-- PRD-002 en BOD-001
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 150, 10, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-002'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );
EOF

# --- systemd service for Gunicorn on 0.0.0.0:8080 ---
cat >/etc/systemd/system/gunicorn.service <<'UNIT'
[Unit]
Description=Gunicorn Django service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/arquisoft/ProyectoArquisoftHermonitos
Environment="PATH=/opt/arquisoft/ProyectoArquisoftHermonitos/.venv/bin"
ExecStart=/opt/arquisoft/ProyectoArquisoftHermonitos/.venv/bin/gunicorn \
  --workers 2 \
  --timeout 120 \
  --bind 0.0.0.0:8080 \
  proyectoArquisoft.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable gunicorn
systemctl start gunicorn
