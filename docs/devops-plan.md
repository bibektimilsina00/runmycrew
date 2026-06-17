# Fuse — Production DevOps Plan

> **Status:** draft for review. Not yet implemented.
> **Owner:** Bibek
> **Target:** single-VPS production deploy on `fuse.bibektimilsina.tech`
> (DigitalOcean droplet, currently 2 GB → recommend upgrade to 4 GB)

---

## 1. Goals + non-goals

### Goals

- Get Fuse live on a production VPS with HTTPS, Google OAuth callbacks working, and zero manual server config drift.
- Containerise every service so the same image runs locally, in CI, and in prod.
- CI/CD via GitHub Actions → ghcr.io. Push to `main` builds + publishes; VPS pulls.
- Repeatable deploys: one `./deploy.sh` on the VPS.
- Reliable backups + tested restore path.
- Logs + healthchecks that surface failures without me babysitting the box.
- Resource ceilings so one runaway container never OOMs the host.

### Non-goals (deferred)

- Kubernetes. Single VPS doesn't justify it. Switch trigger: ~1k DAU or multi-region.
- Multi-region replication.
- Auto-deploy from CI (manual gate stays for now — safer while iterating).
- Blue/green or canary. Compose rolling restart is enough for v1.
- Dedicated vector DB. pgvector covers Fuse for the foreseeable future.
- Image-signing / Cosign. Worth it for an enterprise sale; premature now.

---

## 2. Tech stack (recap)

| Layer | Tech |
|---|---|
| Backend | Python 3.13, FastAPI, uvicorn, SQLAlchemy async, Alembic, Pydantic v2 |
| Workers | Celery 5 (worker + beat) |
| DB | Postgres 15 + pgvector (RAG for Knowledge node) |
| Cache + broker | Redis 7 |
| Frontend | React 19, Vite, TypeScript, Tailwind, pnpm |
| Package mgr (Py) | uv (Astral) — workspace + uv.lock |
| Reverse proxy | Caddy 2 (auto-HTTPS via Let's Encrypt) |
| Registry | ghcr.io (GitHub Container Registry) |
| CI | GitHub Actions |
| Domain | `fuse.bibektimilsina.tech` |

---

## 3. Production architecture

```
                Internet
                   │
                   ▼
        ┌─────────────────────┐
        │     Caddy (web)     │  ports 80, 443 → host
        │ (HTTPS, br + gzip)  │  auto-Let's Encrypt
        └─────────┬───────────┘
                  │
       ┌──────────┼──────────┐
       │                     │
       ▼                     ▼
   /         /api/*    (matched in Caddyfile)
       │                     │
       ▼                     ▼
   static dist           api:8000
   (baked into          ┌────────────────┐
    web image)          │   FastAPI      │  alembic on entrypoint
                        │   uvicorn      │
                        └────┬───────┬───┘
                             │       │
              ┌──────────────┘       └──────────┐
              ▼                                  ▼
        ┌──────────┐                       ┌──────────┐
        │ postgres │  ◀── celery beat ────▶│  redis   │
        │ pgvector │  ◀── celery worker ──▶│ (broker  │
        │  pg15    │     reads + writes    │  + cache)│
        └────┬─────┘                       └──────────┘
             │
             ▼
       pg_backups volume
       (nightly pg_dump cron, 14-day retention)
```

### Service list (7 containers)

| Service | Image | Restart | Memory cap | Notes |
|---|---|---|---|---|
| `web` | `ghcr.io/<owner>/fuse-web:<tag>` (Caddy + dist baked in) | unless-stopped | 128M | Ports 80/443 → host. Single image, no shared volume. |
| `api` | `ghcr.io/<owner>/fuse-api:<tag>` | unless-stopped | 512M | Entrypoint runs `alembic upgrade head` then `exec uvicorn`. |
| `worker` | `ghcr.io/<owner>/fuse-worker:<tag>` | unless-stopped | 384M | Celery worker. |
| `beat` | `ghcr.io/<owner>/fuse-worker:<tag>` (same image, different cmd) | unless-stopped | 128M | `celery -A apps.worker.app.jobs.tasks beat`. |
| `db` | `pgvector/pgvector:pg15` | unless-stopped | 512M | Tuned `shared_buffers`/`work_mem` for the cap. |
| `redis` | `redis:7-alpine` | unless-stopped | 128M | `appendonly yes` for durability. |
| `backup` | `postgres:15-alpine` (just for `pg_dump`) | unless-stopped | 64M | Cron loop: nightly dump + 14-day prune. |

**Total budget ≈ 1.8 GB → 2 GB VPS leaves ~200 MB for OS/network buffers.** Tight. Recommend upgrade to **4 GB before LLM workloads scale**.

---

## 4. Repo additions

```
fuse_monorepo/
├── apps/
│   ├── api/
│   │   ├── Dockerfile               # ← UPDATE: multi-stage, non-root, entrypoint
│   │   └── entrypoint.sh            # ← NEW: alembic + exec uvicorn
│   ├── worker/
│   │   └── Dockerfile               # ← UPDATE: non-root user
│   └── web/
│       ├── Dockerfile               # ← NEW: Node 22 build → Caddy 2 final
│       └── Caddyfile                # ← NEW: routes + HTTPS + headers
├── deploy/
│   ├── docker-compose.production.yml  # ← NEW
│   ├── .env.production.example        # ← NEW (commit example only)
│   ├── deploy.sh                      # ← NEW: pull + restart on VPS
│   ├── backup.sh                      # ← NEW: pg_dump + retention
│   ├── restore.sh                     # ← NEW: tested restore drill
│   └── pg-init/
│       └── 01_extensions.sql          # ← NEW: CREATE EXTENSION vector
├── .github/
│   └── workflows/
│       ├── build-publish.yml          # ← NEW: build + push on main
│       └── ci.yml                     # ← optional: pytest + typecheck on PR
└── docs/
    ├── devops-plan.md                 # this file
    ├── deploy.md                      # ← NEW: operator runbook
    └── secrets.md                     # ← NEW: where each secret lives
```

---

## 5. Image plan (Dockerfiles)

### 5.1 `apps/web/Dockerfile` (new — multi-stage, ~25 MB final)

```dockerfile
# ── stage 1: build static dist ──
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json ./apps/web/
RUN pnpm install --frozen-lockfile
COPY apps/web ./apps/web
WORKDIR /app/apps/web
RUN pnpm build               # vite build → /app/apps/web/dist

# ── stage 2: caddy + dist baked in ──
FROM caddy:2-alpine
COPY --from=build /app/apps/web/dist /srv
COPY apps/web/Caddyfile /etc/caddy/Caddyfile
EXPOSE 80 443
HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget --spider -q http://localhost/healthz || exit 1
```

### 5.2 `apps/web/Caddyfile`

```caddy
{
    email <YOUR_EMAIL_FOR_LE_NOTICES>
}

fuse.bibektimilsina.tech {
    encode gzip zstd

    # static frontend
    root * /srv
    file_server

    # /healthz for the web container's own healthcheck (no upstream call)
    @healthz path /healthz
    respond @healthz 200

    # everything under /api → fastapi
    @api path /api/* /ws/* /openapi.json /docs /redoc
    handle @api {
        reverse_proxy api:8000 {
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
        }
    }

    # SPA fallback — every other route hits index.html
    try_files {path} /index.html

    # Long-cache for hashed Vite assets
    @assets path /assets/*
    header @assets Cache-Control "public, max-age=31536000, immutable"
    # No cache for index.html
    @index path /index.html /
    header @index Cache-Control "no-cache"

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options    "nosniff"
        X-Frame-Options           "DENY"
        Referrer-Policy           "strict-origin-when-cross-origin"
    }

    # Drop the default Caddy `Server: Caddy` banner
    header -Server
}
```

### 5.3 `apps/api/Dockerfile` (update — multi-stage, non-root)

Changes vs current:
- Multi-stage so the runtime image doesn't carry `uv` install caches.
- Non-root `app` user.
- Copy + use `entrypoint.sh`.
- Healthcheck pre-set (compose can override).

```dockerfile
FROM python:3.13-slim AS build
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/worker/pyproject.toml ./apps/worker/
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
RUN uv sync --frozen --no-dev

FROM python:3.13-slim
WORKDIR /app
RUN useradd -r -u 10001 -m -d /home/app app \
 && apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
COPY --from=build /app /app
COPY apps/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown -R app:app /app
USER app
ENV PYTHONPATH=/app PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "--no-sync", "uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.4 `apps/api/entrypoint.sh` (new)

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Apply migrations idempotently (creates vector ext on first run via Alembic op).
uv run --no-sync alembic -c apps/api/alembic.ini upgrade head

# 2. Hand off to the actual CMD (uvicorn).
exec "$@"
```

### 5.5 `apps/worker/Dockerfile` (update — non-root, no entrypoint)

Same multi-stage shape as the API image, no entrypoint script. Compose sets the CMD for worker vs beat.

---

## 6. `docker-compose.production.yml` (new)

Single file, lives in `deploy/`. Run from there: `docker compose -f docker-compose.production.yml up -d`.

Key features:
- Pulls images from ghcr (no `build:` lines).
- Per-service mem_limit + log rotation + restart policy.
- Healthchecks on every service.
- Volumes for data: `postgres_data`, `redis_data`, `caddy_data`, `caddy_config`, `pg_backups`.
- Bind-mounts `./pg-init` for the pgvector extension on first DB boot.
- `.env` (NOT committed) holds all secrets.

```yaml
x-logging: &default-logging
  driver: json-file
  options: { max-size: "10m", max-file: "3" }

services:
  web:
    image: ghcr.io/${GITHUB_OWNER}/fuse-web:${FUSE_IMAGE_TAG:-latest}
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    volumes:
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      api: { condition: service_healthy }
    mem_limit: 128m
    logging: *default-logging

  api:
    image: ghcr.io/${GITHUB_OWNER}/fuse-api:${FUSE_IMAGE_TAG:-latest}
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_SERVER: db
      REDIS_HOST: redis
      ENVIRONMENT: production
      BASE_URL: https://fuse.bibektimilsina.tech
      TZ: UTC
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    mem_limit: 512m
    logging: *default-logging

  worker:
    image: ghcr.io/${GITHUB_OWNER}/fuse-worker:${FUSE_IMAGE_TAG:-latest}
    restart: unless-stopped
    env_file: .env
    environment: { POSTGRES_SERVER: db, REDIS_HOST: redis, TZ: UTC }
    depends_on:
      db:    { condition: service_healthy }
      redis: { condition: service_healthy }
      api:   { condition: service_healthy }
    command: ["uv","run","--no-sync","celery","-A","apps.worker.app.jobs.tasks","worker","--loglevel=info","--concurrency=2"]
    healthcheck:
      test: ["CMD-SHELL", "uv run --no-sync celery -A apps.worker.app.jobs.tasks inspect ping -d celery@$$HOSTNAME || exit 1"]
      interval: 60s
      timeout: 15s
      retries: 3
      start_period: 60s
    mem_limit: 384m
    logging: *default-logging

  beat:
    image: ghcr.io/${GITHUB_OWNER}/fuse-worker:${FUSE_IMAGE_TAG:-latest}
    restart: unless-stopped
    env_file: .env
    environment: { POSTGRES_SERVER: db, REDIS_HOST: redis, TZ: UTC }
    depends_on:
      db:    { condition: service_healthy }
      redis: { condition: service_healthy }
    command: ["uv","run","--no-sync","celery","-A","apps.worker.app.jobs.tasks","beat","--loglevel=info"]
    healthcheck:
      test: ["CMD-SHELL", "pgrep -f 'celery.*beat' >/dev/null || exit 1"]
      interval: 60s
      timeout: 5s
      retries: 3
    mem_limit: 128m
    logging: *default-logging

  db:
    image: pgvector/pgvector:pg15
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_INITDB_ARGS: "--auth=scram-sha-256"
      TZ: UTC
    command:
      - "postgres"
      - "-c"
      - "shared_buffers=128MB"
      - "-c"
      - "effective_cache_size=384MB"
      - "-c"
      - "work_mem=8MB"
      - "-c"
      - "max_connections=50"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./pg-init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    mem_limit: 512m
    logging: *default-logging

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes", "--maxmemory", "96mb", "--maxmemory-policy", "allkeys-lru"]
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    mem_limit: 128m
    logging: *default-logging

  backup:
    image: postgres:15-alpine
    restart: unless-stopped
    env_file: .env
    environment: { TZ: UTC }
    depends_on: { db: { condition: service_healthy } }
    volumes:
      - pg_backups:/backups
      - ./backup.sh:/usr/local/bin/backup.sh:ro
    entrypoint: ["/bin/sh","-c","while true; do /usr/local/bin/backup.sh; sleep 86400; done"]
    mem_limit: 64m
    logging: *default-logging

volumes:
  postgres_data:
  redis_data:
  caddy_data:
  caddy_config:
  pg_backups:
```

---

## 7. `deploy/.env.production.example`

```env
# ─── App ────────────────────────────────────────────────────────────────
PROJECT_NAME=Fuse
API_V1_STR=/api/v1
BASE_URL=https://fuse.bibektimilsina.tech
FRONTEND_URL=https://fuse.bibektimilsina.tech

# ─── Image tag (pin a SHA in prod; use latest only for staging) ─────────
GITHUB_OWNER=bibektimilsina00
FUSE_IMAGE_TAG=latest

# ─── Security (REQUIRED — generate fresh) ───────────────────────────────
# openssl rand -hex 32
SECRET_KEY=
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# ─── Postgres ───────────────────────────────────────────────────────────
POSTGRES_USER=fuse
POSTGRES_PASSWORD=
POSTGRES_DB=fuse

# ─── Redis ──────────────────────────────────────────────────────────────
REDIS_HOST=redis
REDIS_PORT=6379

# ─── SMTP (optional) ────────────────────────────────────────────────────
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_FROM_NAME=Fuse
SMTP_TLS=true

# ─── OAuth providers (only fill what you actually use) ──────────────────
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
META_APP_ID=
META_APP_SECRET=
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
NOTION_CLIENT_ID=
NOTION_CLIENT_SECRET=
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
LINEAR_CLIENT_ID=
LINEAR_CLIENT_SECRET=

# ─── AI providers (only fill what you use) ──────────────────────────────
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
PERPLEXITY_API_KEY=
```

---

## 8. CI/CD — `.github/workflows/build-publish.yml`

Triggers: push to `main`. Builds 3 images in matrix → tags `:latest`, `:sha-<short>`, `:branch-main` → pushes to ghcr. Uses Actions cache for layers (~70% faster after the first run).

```yaml
name: build-publish

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  packages: write   # required to push to ghcr.io

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - service: api
            dockerfile: apps/api/Dockerfile
          - service: worker
            dockerfile: apps/worker/Dockerfile
          - service: web
            dockerfile: apps/web/Dockerfile

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository_owner }}/fuse-${{ matrix.service }}
          tags: |
            type=raw,value=latest
            type=sha,prefix=sha-,format=short
            type=ref,event=branch

      - uses: docker/build-push-action@v6
        with:
          context: .
          file: ${{ matrix.dockerfile }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64
```

> After the first run: GitHub → Settings → Packages → make `fuse-api`/`fuse-worker`/`fuse-web` **public** (otherwise VPS gets 401).

---

## 9. VPS bootstrap (one-time)

Document in `docs/deploy.md`. Concrete steps:

1. DNS A record: `fuse` → `139.59.71.226`, TTL 300.
2. SSH in: `fv` (alias already set up).
3. Install Docker (official one-liner):
   ```
   curl -fsSL https://get.docker.com | sh
   ```
4. Add user (or stay on root for now):
   ```
   usermod -aG docker $USER
   ```
5. Open firewall: `ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw enable`.
6. Pull repo:
   ```
   mkdir -p /opt/fuse && cd /opt/fuse
   git clone https://github.com/bibektimilsina00/fuse_monorepo.git .
   cp deploy/.env.production.example deploy/.env
   nano deploy/.env       # fill all secrets
   chmod 600 deploy/.env
   ```
7. Edit `apps/web/Caddyfile` line 1 → add real email for LE.
8. First boot:
   ```
   cd deploy
   docker compose -f docker-compose.production.yml pull
   docker compose -f docker-compose.production.yml up -d
   docker compose -f docker-compose.production.yml logs -f web api
   ```
9. Hit `https://fuse.bibektimilsina.tech/health` → should return JSON.
10. **Update OAuth redirect URIs** in every provider console (Google, Meta, Slack, etc.) to `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/<service>/callback`.

---

## 10. Everyday deploy flow

After bootstrap, every release is:

```bash
# locally
git push origin main          # triggers Actions build → ghcr

# on VPS (via `fv`)
cd /opt/fuse/deploy
./deploy.sh                   # pulls latest image, restarts only changed services
```

`deploy.sh` does:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
git pull --ff-only            # for docker-compose.production.yml + Caddyfile updates
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d --remove-orphans
docker image prune -f
echo "✓ Fuse updated to $(git rev-parse --short HEAD)"
```

---

## 11. Backups

`deploy/backup.sh` (runs nightly inside `backup` service):

```bash
#!/bin/sh
set -e
TS=$(date -u +%Y%m%d-%H%M%S)
DUMP="/backups/fuse-${TS}.sql.gz"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --no-owner --no-acl --format=custom \
  | gzip > "$DUMP"

# 14-day retention
find /backups -name 'fuse-*.sql.gz' -mtime +14 -delete

echo "[$(date -u)] Backup written: $DUMP"
```

`deploy/restore.sh` (tested restore drill):

```bash
#!/usr/bin/env bash
set -euo pipefail
DUMP="${1:?usage: ./restore.sh <path/to/dump.sql.gz>}"
gunzip -c "$DUMP" | docker compose -f docker-compose.production.yml exec -T db \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner
```

**Drill schedule:** restore the latest dump into a `fuse_restore_test` DB monthly — doc the checklist in `deploy.md`.

**Off-VPS sync (recommended add-on):**
Nightly rsync `/var/lib/docker/volumes/fuse_pg_backups/_data` to:
- DO Spaces (S3-compatible), or
- Backblaze B2 (cheap), or
- A second VPS / your laptop on a schedule

One-line cron entry; doc in deploy.md.

---

## 12. Rollback

Every image is tagged with `:sha-<short>` in ghcr. Rollback:

```bash
# on VPS
export FUSE_IMAGE_TAG=sha-abc1234        # pick from ghcr / Actions logs
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d
```

Add the env var to `.env` to make it stick.

DB rollback: separate concern — if Alembic migrated forward, `alembic downgrade <rev>` from inside the api container. Doc each migration's reversibility.

---

## 13. Observability

### v1 (ship with this)

- `docker compose logs -f <service>` for live tail.
- json-file log driver with `max-size: 10m, max-file: 3` per service (config above).
- Healthchecks on every service.
- `/health` endpoint on FastAPI (already exists).
- Sentry SDK on backend + frontend if you wire DSN into `.env` (frontend already imports `@sentry/react`).

### v2 (add when you start trafficking)

- Uptime monitor (BetterStack / UptimeRobot free tier) hitting `/health` every minute.
- Add Prometheus + Grafana stack only if you want metrics dashboards. Skip until you actually need them.
- ship logs to Loki / Papertrail if you need search.

---

## 14. Security checklist

| Item | Status in this plan |
|---|---|
| HTTPS via Let's Encrypt | ✅ Caddy auto |
| HSTS + standard security headers | ✅ Caddyfile |
| Non-root container users | ✅ api + worker |
| Secrets only in `.env` on VPS, never in repo | ✅ |
| `chmod 600 .env` | ✅ documented |
| Strong Postgres password | ✅ `--auth=scram-sha-256` + generated pw |
| Encryption key for credentials at rest | ✅ Fernet (existing) |
| Firewall (ufw 22/80/443 only) | ✅ documented |
| SSH key-only login (disable password auth) | ✅ documented |
| OAuth callback URLs updated | ✅ deploy.md checklist |
| Log redaction (API keys in URLs) | ✅ already done in `llm.py` |
| Rate-limiting on API | ⚠️ deferred to phase 2 |
| Web Application Firewall (Cloudflare proxy) | ⚠️ deferred to phase 2 |

---

## 15. Migration story (Alembic + pgvector)

- `entrypoint.sh` runs `alembic upgrade head` on every api boot. Single-instance only — safe today.
- pgvector extension: confirm there's an Alembic op doing `CREATE EXTENSION IF NOT EXISTS vector;` early in the chain. Belt-and-suspenders: `deploy/pg-init/01_extensions.sql` runs once on first DB init (when the volume is empty).
- When you scale to 2+ api containers in the future: introduce an `init` one-shot container that runs `alembic upgrade head` and exits, then api containers `depends_on: { init: { condition: service_completed_successfully } }`. Defer until you actually scale.

---

## 16. Phase plan

| Phase | Goal | What ships |
|---|---|---|
| **P0 — bootstrap (today)** | Get the stack running on VPS with HTTPS + Google OAuth. | All the files above; manual deploy. |
| **P1 — hardening** | Backup off-VPS, monitor, alerts. | Rsync to B2/S3, BetterStack uptime, Sentry DSN wired. |
| **P2 — auto-deploy (optional)** | Push to main → live. | Actions SSH to VPS + run `./deploy.sh`. Add manual gate via environment protection. |
| **P3 — scale** | Outgrow single VPS. | DO Managed Postgres, second VPS for workers, Cloudflare in front, eventually k8s. |

Don't pre-build for P2/P3. Move when the pain shows up.

---

## 17. Open questions for you

1. **Email for Let's Encrypt notices** — which address? (Goes in Caddyfile line 1.)
2. **VPS size** — stay at 2 GB and hope, or bump to 4 GB ($24/mo) before launch? Strong recommend the bump.
3. **Sentry DSN** — have one set up, or skip for v1?
4. **Off-VPS backups** — DO Spaces, Backblaze B2, or rsync to a second machine? Want this in P0 or P1?
5. **Staging environment** — single prod for now, or separate `staging.fuse.bibektimilsina.tech`? (Adds complexity but catches breakage before users see it.)

---

## 18. What I'll build when you approve

In one PR:

1. `apps/api/Dockerfile` + `entrypoint.sh` (update)
2. `apps/worker/Dockerfile` (update — non-root)
3. `apps/web/Dockerfile` + `Caddyfile` (new)
4. `deploy/docker-compose.production.yml` (new)
5. `deploy/.env.production.example` (new)
6. `deploy/deploy.sh` + `backup.sh` + `restore.sh` (new)
7. `deploy/pg-init/01_extensions.sql` (new)
8. `.github/workflows/build-publish.yml` (new)
9. `docs/deploy.md` (new — operator runbook)
10. `docs/secrets.md` (new — where every secret lives)

After merge, I'll walk you through the one-time VPS bootstrap.

---

**Sign off:**

- Plan: ☐ approved / ☐ revisions wanted
- Open question answers below this line:
  - Email:
  - VPS size:
  - Sentry:
  - Off-VPS backups:
  - Staging env:
