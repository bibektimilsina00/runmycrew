# syntax=docker/dockerfile:1.7

# ── Stage 1 ─ resolve the uv workspace and stage runtime files ──────────
FROM python:3.13-slim AS build

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Bring in the uv binary from upstream.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Workspace metadata first so layer caching survives code edits.
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/worker/pyproject.toml ./apps/worker/

# Application code. API depends on worker imports for Celery enqueue.
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

# Resolve the full workspace environment from the frozen lock — prod
# only (no dev extras).
RUN uv sync --frozen --no-dev

# ── Stage 2 ─ slim runtime image, non-root user ─────────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# `curl` is used by the docker healthcheck. Everything else stays out.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid app --home /home/app --create-home app

WORKDIR /app

# Copy the built environment + sources from the build stage.
COPY --from=build --chown=app:app /app /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Entrypoint script: runs Alembic migrations, then execs the CMD.
COPY --chown=app:app apps/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "--no-sync", "uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
