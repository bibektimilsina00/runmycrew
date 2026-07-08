# Development

## Requirements

[pnpm](https://pnpm.io/), Node.js 24+, [uv](https://astral.sh/uv), Python 3.13,
PostgreSQL 15+ (pgvector), Redis 7. Docker for the local DB/Redis.

## Setup

```bash
make setup        # pnpm install + uv sync (api, worker) + install pre-commit hooks
cp .env.example .env
openssl rand -hex 32   # set ENCRYPTION_KEY in .env
```

## Run

```bash
make db-up        # Postgres + Redis via docker compose
make migrate      # alembic upgrade head
make api          # FastAPI                — http://localhost:8000
make worker       # Celery worker (separate terminal)
make beat         # Celery beat (schedules) (separate terminal)
make web          # frontend (Vite)        — http://localhost:3001
make site         # marketing site (Next)  — http://localhost:3100
```

The API, worker, and beat run as separate processes. The worker is what actually
executes workflows — see [execution-flow.md](./execution-flow.md).

## Test

```bash
# Backend (from repo root)
PYTHONPATH=. uv run --project apps/api python -m pytest apps/api/tests -q

# Frontend
pnpm --filter runmycrew-web exec tsc -b      # typecheck
pnpm --filter runmycrew-web lint             # eslint
pnpm --filter runmycrew-web build            # production build
```

The backend suite includes a **live execution integration test**
(`test_execution_live.py`) that runs against Postgres + Redis; it skips
automatically when the DB is unreachable, so `make db-up` first to exercise it.

## Lint & format

```bash
make lint         # ruff (Python) + eslint (web)
```

`make setup` installs **pre-commit** hooks (ruff, ruff-format, gitleaks secret
scanning, yaml/json checks, no-commit-to-main). They run on every commit.

## CI

`.github/workflows/ci.yml` runs on push to `main` and all PRs:

- **backend** — spins up Postgres + Redis service containers, applies
  migrations, runs `alembic check` (model-drift gate), then `pytest`.
- **frontend** — `tsc` typecheck, `eslint`, `vite build`.

## Conventions

Absolute imports only; logging via the central logger (no `print`/`console.log`);
backend layering Router → Service → Repository → Model; HTTP contracts as
Pydantic (backend) kept in sync with Zod (frontend). See `AGENTS.md`.
