#!/bin/bash
set -euxo pipefail

# Basic packages
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-venv python3-pip git build-essential libpq-dev

# App home
APP_HOME=/opt/arquisoft
mkdir -p "${APP_HOME}"
cd "${APP_HOME}"

# Clone the repo
if [ ! -d "ProyectoArquisoftHermonitos" ]; then
  git clone "${repo_url}"
fi
cd ProyectoArquisoftHermonitos

# Python venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (Pillow for ImageField, psycopg2 for Postgres)
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
fi
pip install "psycopg2-binary>=2.9" Pillow

# === Write DB settings and make Django use them ===
SETTINGS_DIR="proyectoArquisoft"
SETTINGS_MAIN="${SETTINGS_DIR}/settings.py"
SETTINGS_LOCAL="${SETTINGS_DIR}/settings_local.py"

# Ensure settings.py will import settings_local if present
grep -q "settings_local" "${SETTINGS_MAIN}" || cat >> "${SETTINGS_MAIN}" <<'PYEOF'

# --- auto-included by bootstrap ---
try:
    from .settings_local import *  # noqa
except Exception:
    pass
# --- end auto-included ---
PYEOF

# Write settings_local.py with the RDS connection
cat > "${SETTINGS_LOCAL}" <<PYEOF
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "${db_name}",
        "USER": "${db_user}",
        "PASSWORD": "${db_password}",
        "HOST": "${rds_host}",
        "PORT": "${db_port}",
        "CONN_MAX_AGE": 60,
    }
}
PYEOF

# Run migrations
# Detect manage.py location (repo root holds manage.py in this project)
if [ -f manage.py ]; then
  DJANGO_DIR="."
else
  # fallback: search
  DJANGO_DIR="$(git rev-parse --show-toplevel)"
fi

cd "${DJANGO_DIR}"

#----DB population-------

apt-get install -y postgresql-client

psql "postgresql://${db_user}:${db_password}@${rds_host}:${db_port}/${db_name}" <<'EOF'
-- insert Bodega
INSERT INTO core_bodega (codigo, nombre, ciudad, direccion, capacidad, longitud, latitud)
VALUES ('BOD-001', 'Bodega Central', 'Bogotá', 'Cra 7 # 72-41', 1000.00, -74.060, 4.664)
RETURNING id;

-- insert Ubicacion for that Bodega
INSERT INTO core_ubicacion (codigo, tipo, capacidad_max, dimensiones, estado, bodega_id)
VALUES ('UB-01', 'Estanteria', 200.0, '2mx1mx1m', 'Disponible', 1)
RETURNING id;

-- insert Productos
INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
VALUES ('7701234567890', 'Electronico', 1.5, 0.002, 'PRD-001')
RETURNING id;

INSERT INTO core_producto (codigo_barras, tipo, peso, volumen, codigo)
VALUES ('7700987654321', 'Juguete', 0.3, 0.0005, 'PRD-002')
RETURNING id;

-- insert Inventario for those products at Bodega 1
INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
VALUES (50, 5, NOW(), 1, 1);

INSERT INTO core_inventario (cantidad_disponible, cantidad_reservada, ultima_actualizacion, productos_id, bodegas_id)
VALUES (150, 10, NOW(), 2, 1);
EOF

echo "=== DB populated ==="

nohup python3 manage.py runserver 0.0.0.0:8080 >/var/log/django-runserver.log 2>&1 &