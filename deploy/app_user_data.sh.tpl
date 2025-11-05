#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

# Basic packages
apt-get update
apt-get install -y python3 python3-venv python3-pip git build-essential libpq-dev postgresql-client

APP_HOME=/opt/arquisoft
mkdir -p "$APP_HOME"
cd "$APP_HOME"

# Clone only the requested branch (saves space)
if [ ! -d "ProyectoArquisoftHermonitos" ]; then 
  git clone --branch "${branch}" --single-branch "${repo_url}"
fi
cd ProyectoArquisoftHermonitos

# Python venv
python3 -m venv .venv
source .venv/bin/activate

# Deps
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
fi
pip install "psycopg2-binary>=2.9" Pillow

# Settings override (IMPORTANT: your settings folder is 'proyectoArquisoft')
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

# Write Postgres connection
cat > "$SETTINGS_LOCAL" <<PYEOF
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
PYEOF

# ensure database exists
for i in {1..20}; do
    if psql "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/postgres" -c "CREATE DATABASE ${db_name};" >/dev/null 2>&1; then
        echo "Database ${db_name} exists"
        break
    fi
    echo "Waiting for DB to accept CREATE DATABASE... ($i/20)"
    sleep 3
done

# Run migrations
if [ -f manage.py ]; then
  DJANGO_DIR="."
else
  DJANGO_DIR="$(git rev-parse --show-toplevel)"
fi

cd "$DJANGO_DIR"

python3 manage.py migrate --noinput || (sleep 5 && python3 manage.py migrate --noinput)

# --- Seed minimal test data for: Bodega, Ubicacion, Producto, Inventario ---
psql "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/${db_name}" -v ON_ERROR_STOP=1 <<'EOF'
-- Bodega
INSERT INTO core_bodega (codigo, nombre, ciudad, direccion, capacidad, longitud, latitud)
VALUES ('BOD-001', 'Bodega Central', 'Bogotá', 'Cra 7 # 72-41', 1000.00, -74.060, 4.664)
ON CONFLICT DO NOTHING;

-- Ubicacion (assumes bodega id 1 in an empty DB; adjust if needed)
INSERT INTO core_ubicacion (codigo, tipo, capacidad_max, dimensiones, estado, bodega_id)
VALUES ('UB-01', 'Estanteria', 200.0, '2mx1mx1m', 'Disponible', 1)
ON CONFLICT DO NOTHING;

-- Productos
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
VALUES ('7701234567890', 'Electronico', 1.5, 0.002, 'PRD-001')
ON CONFLICT DO NOTHING;

INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
VALUES ('7700987654321', 'Juguete', 0.3, 0.0005, 'PRD-002')
ON CONFLICT DO NOTHING;

-- Inventario (product ids 1,2 and bodega 1 in a fresh DB)
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
VALUES (50, 5, NOW(), 1, 1);

INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
VALUES (150, 10, NOW(), 2, 1);
EOF

# Run dev server on 8080
nohup python3 manage.py runserver 0.0.0.0:8080 >/var/log/django-runserver.log 2>&1 &