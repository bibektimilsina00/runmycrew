#!/usr/bin/env bash
# Launch the full local dev stack: db + redis + migrations + api + worker + beat + web + site.
#
# One terminal, all five Python/Node processes streamed with coloured prefixes.
# Ctrl-C kills the whole tree cleanly via a trap on SIGINT/SIGTERM.
#
# Requires: docker + docker-compose, uv, pnpm. Run from the repo root.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ── Colours for log prefixes ────────────────────────────────────────
C_RESET="\033[0m"
C_API="\033[36m"     # cyan
C_WORKER="\033[33m"  # yellow
C_BEAT="\033[35m"    # magenta
C_WEB="\033[32m"     # green
C_SITE="\033[34m"    # blue
C_SYS="\033[1;37m"   # bold white
C_ERR="\033[1;31m"   # bold red

log()  { printf "${C_SYS}[dev]${C_RESET} %s\n" "$*"; }
fail() { printf "${C_ERR}[dev]${C_RESET} %s\n" "$*" >&2; exit 1; }

# ── Pre-flight checks ───────────────────────────────────────────────
command -v docker  >/dev/null || fail "docker not installed"
command -v uv      >/dev/null || fail "uv not installed (see https://docs.astral.sh/uv)"
command -v pnpm    >/dev/null || fail "pnpm not installed"

# .env must exist for native (non-docker) api/worker — they read POSTGRES_SERVER etc.
if [[ ! -f apps/api/.env ]]; then
  fail "apps/api/.env missing — copy apps/api/.env.example and fill in secrets first"
fi

# ── Infrastructure ──────────────────────────────────────────────────
log "starting Postgres + Redis via docker-compose…"
docker compose up -d db redis >/dev/null

log "waiting for Postgres to accept connections…"
for _ in {1..30}; do
  if docker compose exec -T db pg_isready -U postgres >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

log "running alembic migrations…"
(cd apps/api && PYTHONPATH=../.. uv run alembic upgrade head)

# ── Process launcher ────────────────────────────────────────────────
PIDS=()

# Stream stdout/stderr of a child with a coloured prefix on every line. The
# prefix label is the process name; the colour distinguishes it visually.
launch() {
  local name="$1" colour="$2"; shift 2
  log "starting $name…"
  (
    "$@" 2>&1 | while IFS= read -r line; do
      printf "${colour}[%s]${C_RESET} %s\n" "$name" "$line"
    done
  ) &
  PIDS+=($!)
}

# ── Trap for clean shutdown ─────────────────────────────────────────
cleanup() {
  local code=$?
  log "shutting down…"
  # Kill every launched process group; tolerate "already gone".
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    fi
  done
  # Don't propagate non-zero exit on Ctrl-C — that's the user's choice.
  [[ $code -eq 130 ]] && exit 0 || exit "$code"
}
trap cleanup INT TERM EXIT

# ── Launch the five workers ────────────────────────────────────────
# API: FastAPI with --reload so code changes hot-reload.
launch api    "$C_API"    bash -c "cd apps/api    && PYTHONPATH=../.. uv run uvicorn app.main:app --reload --port 8000"

# Worker: Celery worker pulling jobs (executions, polling triggers, etc).
launch worker "$C_WORKER" bash -c "cd apps/worker && PYTHONPATH=../.. uv run celery -A app.jobs.tasks worker --loglevel=info"

# Beat: Celery beat publishing cron-trigger ticks. Required for agent loops.
launch beat   "$C_BEAT"   bash -c "cd apps/api    && PYTHONPATH=../.. uv run celery -A apps.api.app.core.celery beat --loglevel=info"

# Frontends: filter through pnpm so turbo doesn't try to start them too.
launch web    "$C_WEB"    pnpm --filter web  dev
launch site   "$C_SITE"   pnpm --filter site dev

log "all services launched. URLs:"
log "  api    → http://localhost:8000  (docs: /docs, health: /health)"
log "  web    → http://localhost:5173"
log "  site   → http://localhost:3000"
log ""
log "press Ctrl-C to stop everything."

# Wait for any child to exit. If one dies, surface its code so the user notices.
wait -n
fail "one of the services exited unexpectedly — check the logs above"
