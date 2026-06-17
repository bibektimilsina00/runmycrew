# syntax=docker/dockerfile:1.7

# Shared image for the Celery worker AND beat scheduler — the compose
# stack sets a different `command` for each service. One image, two
# roles. Keeps ghcr storage and CI matrix small.

FROM python:3.14-slim AS build

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/worker/pyproject.toml ./apps/worker/

# Worker executes via apps.api modules (engine, models, credential mgr).
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

RUN uv sync --frozen --no-dev

# ── Runtime ─────────────────────────────────────────────────────────────
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# `procps` for the `pgrep` healthcheck on celery beat.
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid app --home /home/app --create-home app

WORKDIR /app

COPY --from=build --chown=app:app /app /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

USER app

# Default CMD = worker. Compose overrides for beat. Either way runs as
# a non-root process from the same image.
CMD ["uv", "run", "--no-sync", "celery", "-A", "apps.worker.app.jobs.tasks", "worker", "--loglevel=info", "--concurrency=2"]
