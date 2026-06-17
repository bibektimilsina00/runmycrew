#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Fuse API container entrypoint
#
# 1. Apply pending Alembic migrations idempotently. Safe to re-run on
#    every container start; no-op when the schema is already at head.
# 2. Exec the CMD (defaults to uvicorn). `exec` replaces this shell
#    so PID 1 stays the actual process — Docker stop signals reach it.
# ----------------------------------------------------------------------
set -euo pipefail

echo "[entrypoint] Applying database migrations…"
uv run --no-sync alembic -c apps/api/alembic.ini upgrade head
echo "[entrypoint] Migrations done."

echo "[entrypoint] Handing off to: $*"
exec "$@"
