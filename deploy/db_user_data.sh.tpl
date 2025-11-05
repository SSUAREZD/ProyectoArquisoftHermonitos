#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y curl ca-certificates gnupg lsb-release

# Add PGDG repo for Postgres 16 on Ubuntu
install -d /usr/share/postgresql-common/pgdg
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg
sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

apt-get update
apt-get install -y postgresql-16

# Listen on all interfaces
PGVER=16
PGCONF="/etc/postgresql/$PGVER/main/postgresql.conf"
PGHBA="/etc/postgresql/$PGVER/main/pg_hba.conf"

sed -i "s/^#*listen_addresses.*/listen_addresses = '0.0.0.0'/" "$PGCONF"

# Allow the whole VPC CIDR with md5 (network is still restricted by SG to the app EC2 only)
echo "host all all ${vpc_cidr} md5" >> "$PGHBA"

systemctl enable postgresql
systemctl restart postgresql

# Create role and database
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'Administrator') THEN
    CREATE ROLE "Administrator" LOGIN PASSWORD '${db_password}';
  END IF;
END\$\$;

-- create DB if not exists and set owner
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '${db_name}') THEN
    CREATE DATABASE ${db_name} OWNER "Administrator";
  ELSE
    ALTER DATABASE ${db_name} OWNER TO "Administrator";
  END IF;
END\$\$;
SQL