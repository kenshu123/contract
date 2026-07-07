#!/bin/sh
set -e

if [ -z "$DB_HOST" ]; then
  echo "ERROR: DB_HOST is not set"
  exit 1
fi

export PGPASSWORD="$DB_PASSWORD"
PSQL="psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME"

echo "[migrate] START $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "[migrate] Running init.sql..."
$PSQL -f /app/init.sql
echo "[migrate] init.sql done."

echo "[migrate] Running migrate_add_content_hash.sql..."
$PSQL -f /app/migrate_add_content_hash.sql
echo "[migrate] migrate_add_content_hash.sql done."

echo "[migrate] COMPLETE $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
