.PHONY: setup db-up migrate api worker beat web site lint clean

# ── One-time setup ──────────────────────────────────────────────────
setup:
	pnpm install
	cd apps/api && uv sync
	cd apps/worker && uv sync
	uvx pre-commit install

# ── Local dev (run each in its own terminal) ────────────────────────
db-up:
	docker-compose up -d db redis

migrate:
	cd apps/api && PYTHONPATH=../.. uv run alembic upgrade head

api:
	cd apps/api && PYTHONPATH=../.. uv run uvicorn app.main:app --reload --port 8000

worker:
	cd apps/worker && PYTHONPATH=../.. uv run celery -A app.jobs.tasks worker --loglevel=info

beat:
	cd apps/api && PYTHONPATH=../.. uv run celery -A apps.api.app.core.celery beat --loglevel=info

web:
	pnpm --filter runmycrew-web dev

site:
	pnpm --filter runmycrew-site dev

# ── Utilities ───────────────────────────────────────────────────────
lint:
	uv run --project apps/api ruff check . --fix
	uv run --project apps/api ruff format .
	pnpm --filter runmycrew-web lint

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
