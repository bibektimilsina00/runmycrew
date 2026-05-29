.PHONY: setup dev build-web lint lint-py lint-js type-check test clean db-up migrate docker-build docker-up beat

setup:
	pnpm install
	cd apps/api && uv sync
	cd apps/worker && uv sync
	uvx pre-commit install

dev:
	pnpm dev

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

dev-all:
	make db-up
	make migrate
	@echo "🚀 Infrastructure ready. Starting frontend..."
	@echo "💡 Note: You still need to run 'make api' and 'make worker' in separate tabs."
	pnpm dev

lint: lint-py lint-js

lint-py:
	uv run --project apps/api ruff check . --fix
	uv run --project apps/api ruff format .

lint-js:
	pnpm --filter web lint

type-check:
	pnpm --filter web exec tsc --noEmit

build-web:
	pnpm --filter web run build

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
