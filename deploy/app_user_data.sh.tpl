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
COGNITO_APP_CLIENT_ID = "593e5kv7f4fm12vmpldkfbe85e"
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

# ---  population ---
psql "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/${db_name}" -v ON_ERROR_STOP=1 <<'EOF' || true
BEGIN;
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

-- Coca-Cola 1.5L
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7705001000001', 'Bebida', 1.5, 0.0015, 'PRD-003'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-003' OR codigo_barras = '7705001000001'
);

-- Arroz Diana 5kg
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7702002000002', 'Alimento', 5.0, 0.0045, 'PRD-004'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-004' OR codigo_barras = '7702002000002'
);

-- Taladro Bosch GSB 13 RE
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7709003000003', 'Herramienta', 1.8, 0.0032, 'PRD-005'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-005' OR codigo_barras = '7709003000003'
);

-- Laptop Lenovo ThinkPad E14
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7708004000004', 'Electrónico', 1.6, 0.0041, 'PRD-006'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-006' OR codigo_barras = '7708004000004'
);

-- Caja Tornillos 2" x100 unidades
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7703005000005', 'Ferretería', 0.4, 0.0006, 'PRD-007'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-007' OR codigo_barras = '7703005000005'
);

-- Pañales Huggies Etapa 3 (x30)
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7704006000006', 'Higiene', 1.1, 0.0021, 'PRD-008'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-008' OR codigo_barras = '7704006000006'
);

-- Aceite Motul 5100 4T 10W40 (1L)
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
SELECT '7707007000007', 'Automotriz', 1.0, 0.0012, 'PRD-009'
WHERE NOT EXISTS (
  SELECT 1 FROM core_producto
  WHERE codigo = 'PRD-009' OR codigo_barras = '7707007000007'
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

-- PRD-003 Coca-Cola 1.5L
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 120, 10, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-003'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );

-- PRD-004 Arroz Diana 5kg
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 60, 5, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-004'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );

-- PRD-005 Taladro Bosch
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 18, 2, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-005'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );

-- PRD-006 Laptop ThinkPad
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 25, 1, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-006'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );

-- PRD-007 Caja Tornillos
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 200, 15, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-007'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );

-- PRD-008 Pañales Huggies
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 90, 5, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-008'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );

-- PRD-009 Aceite Motul
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
SELECT 40, 3, NOW(), p.id, b.id
FROM core_producto p
JOIN core_bodega b ON b.codigo = 'BOD-001'
WHERE p.codigo = 'PRD-009'
  AND NOT EXISTS (
    SELECT 1 FROM core_inventario i WHERE i.productos_id = p.id AND i.bodegas_id = b.id
  );
COMMIT;
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