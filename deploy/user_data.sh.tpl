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
python3 manage.py migrate --noinput || (sleep 5 && python3 manage.py migrate --noinput)

# OPTIONAL: runserver on 8080 (comment out if you only wanted migrations)
# nohup python3 manage.py runserver 0.0.0.0:8080 >/var/log/django-runserver.log 2>&1 &