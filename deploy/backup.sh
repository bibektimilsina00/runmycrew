#!/bin/sh
# ----------------------------------------------------------------------
# Fuse — nightly Postgres dump
#
# Runs inside the `backup` container in compose; the entrypoint sleeps
# 24h between runs. Writes to /backups (the pg_backups volume).
#
# Format: `pg_dump --format=custom` so `pg_restore` can do selective
# restore later. Gzipped for ~5x size reduction.
#
# Retention: 14 days. Older dumps are removed.
# ----------------------------------------------------------------------
set -e

TS=$(date -u +%Y%m%d-%H%M%S)
DEST="/backups/fuse-${TS}.dump.gz"

echo "[$(date -u +%FT%TZ)] Backup START → ${DEST}"

PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h db -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    --no-owner --no-acl --format=custom \
  | gzip -6 > "${DEST}"

# Track the latest pointer for monitoring scripts.
ln -sf "$(basename "${DEST}")" /backups/latest.dump.gz

# Retention sweep — keep 14 days, delete the rest.
find /backups -name 'fuse-*.dump.gz' -mtime +14 -delete

SIZE=$(stat -c '%s' "${DEST}" 2>/dev/null || stat -f '%z' "${DEST}")
echo "[$(date -u +%FT%TZ)] Backup OK   → ${DEST} (${SIZE} bytes)"
