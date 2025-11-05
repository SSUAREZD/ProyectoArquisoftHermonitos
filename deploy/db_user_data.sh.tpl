#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y curl ca-certificates gnupg lsb-release

install -d /usr/share/postgresql-common/pgdg
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg
echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list

apt-get update
apt-get install -y postgresql-16 postgresql-client-16

PGVER=16
PGCONF="/etc/postgresql/$PGVER/main/postgresql.conf"
PGHBA="/etc/postgresql/$PGVER/main/pg_hba.conf"

sed -i "s/^#*listen_addresses.*/listen_addresses = '0.0.0.0'/" "$PGCONF"

# allow postgres user locally
echo "local   all             postgres                                trust" >> "$PGHBA"
# allow VPC cidr
echo "host    all             all                 ${vpc_cidr}         md5"   >> "$PGHBA"

systemctl restart postgresql
sleep 3

# -------- CREATE USER & DB ---------

# create Admin user if not exists
sudo -u postgres psql -c "CREATE ROLE \"Administrator\" LOGIN PASSWORD '${db_password}'" || true

# create database if not exists
sudo -u postgres psql -c "CREATE DATABASE ${db_name} OWNER \"Administrator\"" || true