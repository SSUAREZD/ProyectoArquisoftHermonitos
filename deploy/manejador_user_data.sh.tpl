#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y python3 python3-venv python3-pip git build-essential libpq-dev postgresql-client

APP_HOME=/opt/manejador
mkdir -p "$APP_HOME"
cd "$APP_HOME"

# Pull branch manejador-pedidos
if [ ! -d "ProyectoArquisoftHermonitos" ]; then 
  git clone --branch "${branch}" --single-branch "${repo_url}"
fi
cd ProyectoArquisoftHermonitos

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
fi
pip install "psycopg2-binary>=2.9" Pillow requests

# Create settings_local WITHOUT CHANGING SECRET_KEY
SETTINGS_DIR="proyectoArquisoft"
SETTINGS_LOCAL="$SETTINGS_DIR/settings_local.py"

cat > "$SETTINGS_LOCAL" <<PYEOF
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "${db_name}",
        "USER": "${db_user}",
        "PASSWORD": "${db_password}",
        "HOST": "${db_host}",
        "PORT": "${db_port}",
    }
}

INVENTARIO_SERVICE_URL = "${inventario_url}"

# Allow external access (required for EC2 public access)
ALLOWED_HOSTS = ["*"]
PYEOF

# Ensure settings.py loads settings_local.py
SETTINGS_MAIN="$SETTINGS_DIR/settings.py"
grep -q "settings_local" "$SETTINGS_MAIN" || cat >> "$SETTINGS_MAIN" <<'EOF'

# Auto-included by bootstrap
try:
    from .settings_local import *
except Exception:
    pass
EOF

# Run migrations
python3 manage.py migrate --noinput || true

# Run server on port 8090
nohup python3 manage.py runserver 0.0.0.0:8090 >/var/log/manejador.log 2>&1 &