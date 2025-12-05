#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

# --- Basic packages ---
apt-get update
apt-get install -y python3 python3-venv python3-pip git build-essential libpq-dev postgresql-client nginx

APP_HOME=/opt/arquisoft
mkdir -p "$APP_HOME"
cd "$APP_HOME"

# --- Clone the branch for INVENTARIO  ---
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
STATIC_ROOT = "/opt/arquisoft/ProyectoArquisoftHermonitos/staticfiles"
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

# ---  population ---   (si tus modelos cambiaron mucho entre ramas, revisa esto luego)
psql "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/${db_name}" -v ON_ERROR_STOP=1 <<'EOF' || true
-- ... (tu SQL de población tal cual lo tenías) ...
EOF

# =================================================================
# ======================= GUNICORN SERVICE ========================
# =================================================================
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
  --bind 127.0.0.1:8080 \
  proyectoArquisoft.wsgi:application

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

# =================================================================
# ======================= NGINX BASE CONFIG =======================
# =================================================================

cat > /etc/nginx/nginx.conf <<'NGINXMAIN'
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    include /etc/nginx/sites-enabled/*;
}
NGINXMAIN

rm -f /etc/nginx/sites-enabled/default || true

cat > /etc/nginx/sites-available/django <<'NGINXCONF'
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /opt/arquisoft/ProyectoArquisoftHermonitos/staticfiles/;
    }
}
NGINXCONF

ln -sf /etc/nginx/sites-available/django /etc/nginx/sites-enabled/django

systemctl daemon-reload
systemctl enable gunicorn
systemctl restart gunicorn

systemctl enable nginx
systemctl restart nginx
