#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Fuse — Postgres restore from a `backup.sh` dump
#
# DESTRUCTIVE: drops + recreates every table in the target DB. Run
# this against a SCRATCH database first to verify the dump actually
# restores cleanly — schedule the drill monthly.
#
# Usage:
#     ./restore.sh /var/lib/docker/volumes/fuse_pg_backups/_data/fuse-20260617-021500.dump.gz
#
# Or restore the most recent:
#     ./restore.sh /var/lib/docker/volumes/fuse_pg_backups/_data/latest.dump.gz
# ----------------------------------------------------------------------
set -euo pipefail

DUMP="${1:-}"
if [[ -z "${DUMP}" || ! -f "${DUMP}" ]]; then
  echo "usage: ./restore.sh <path/to/fuse-*.dump.gz>" >&2
  exit 2
fi

cd "$(dirname "$0")"
COMPOSE_FILE="docker-compose.production.yml"

# Sanity-load .env so POSTGRES_* are visible to this shell.
# shellcheck disable=SC1091
set -a; source .env; set +a

echo "▶ Restoring ${DUMP} → ${POSTGRES_DB}@db"
echo "  This will OVERWRITE existing data. Ctrl+C in 5s to abort."
sleep 5

gunzip -c "${DUMP}" \
  | docker compose -f "${COMPOSE_FILE}" exec -T db \
      pg_restore \
        --username "${POSTGRES_USER}" \
        --dbname "${POSTGRES_DB}" \
        --clean --if-exists --no-owner --no-acl

echo "✓ Restore complete. Verify with:"
echo "  docker compose -f ${COMPOSE_FILE} exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c '\\dt'"
