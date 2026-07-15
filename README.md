<div align="center">

<img src=".github/assets/runmycrew-mark.svg" alt="RunMyCrew" width="72" height="72" />

# RunMyCrew

### Automation in plain English

Describe what you want in a sentence → AI builds the workflow → one click and it's live. No nodes to wire, no glue code, no reading integration docs. Connect 250+ apps, self-host the whole thing, or use the cloud.

<br />

[![Build status](https://img.shields.io/github/actions/workflow/status/bibektimilsina00/runmycrew/build-publish.yml?branch=main&label=build&style=flat-square)](https://github.com/bibektimilsina00/runmycrew/actions)
[![Deploy](https://img.shields.io/github/actions/workflow/status/bibektimilsina00/runmycrew/deploy.yml?branch=main&label=deploy&style=flat-square)](https://github.com/bibektimilsina00/runmycrew/actions)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![ghcr.io](https://img.shields.io/badge/container-ghcr.io-181717?style=flat-square&logo=github)](https://github.com/bibektimilsina00?tab=packages)
[![Caddy](https://img.shields.io/badge/HTTPS-Caddy-1F88C0?style=flat-square)](https://caddyserver.com/)
[![Python](https://img.shields.io/badge/python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-22-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)

<br />

**[🌐 Live app](https://app.runmycrew.com)** · **[🎯 Marketing site](https://runmycrew.com)** · **[📚 Docs](https://runmycrew.com/docs)** · **[🐛 Report a bug](https://github.com/bibektimilsina00/runmycrew/issues/new)**

<br />

> ⚠️ **Early access — very much a work in progress.** RunMyCrew is in early beta: it works end-to-end today, but expect rough edges and breaking changes. Try it, and please [open an issue](https://github.com/bibektimilsina00/runmycrew/issues/new) with feedback — it's what shapes what we build next.

</div>

<br />

---

## 📖 Table of Contents

- [✨ What is RunMyCrew?](#-what-is-runmycrew)
- [🎯 Features](#-features)
- [📸 Showcase](#-showcase)
- [🏗 Architecture](#-architecture)
- [🧰 Tech Stack](#-tech-stack)
- [🚀 Quick Start (self-host)](#-quick-start-self-host)
- [🛠 Development setup](#-development-setup)
- [📁 Project structure](#-project-structure)
- [🔌 Integrations](#-integrations)
- [🎨 Theming](#-theming)
- [🚢 Deployment](#-deployment)
- [🔐 Security](#-security)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)

<br />

## ✨ What is RunMyCrew?

RunMyCrew is an **open-source automation platform** that lives somewhere between Zapier and a workflow IDE. You can:

- **Describe** what you want to automate in plain English and let **Crew AI** (Claude-powered Copilot) turn it into a multi-step workflow.
- **Connect** the apps you already use through battle-tested OAuth flows — Google Workspace, Slack, GitHub, Notion, Stripe, Meta, and more.
- **Run** workflows on a schedule, webhook, or app event with retries, backoff, and per-step payload inspection.
- **Observe** every execution with full logs, run replay, and alerts so you know the moment something drifts.
- **Self-host** the whole stack with a single `docker compose up`, or use the hosted version at [`app.runmycrew.com`](https://app.runmycrew.com).

The codebase is a **pnpm + uv monorepo** with four apps and a shared deploy folder — no microservice maze, no Kubernetes required for v1.

<br />

## 🎯 Features

| | |
|---|---|
| 🤖 **Crew AI** | Generate, refine, and explain workflows with a Claude-powered chat panel inside the editor. |
| 🧩 **Visual node-based builder** | React Flow canvas with typed inputs, expression bindings, conditional branching, and a live inspector. |
| 🔌 **250+ integrations** | GitHub, Slack, Notion, Linear, Google Workspace, Stripe, HubSpot, Salesforce, Jira, Airtable, Meta, OpenAI, Anthropic — plus a long tail (Databricks, Snowflake-adjacent, Shopify, Twilio, Sentry, and hundreds more). |
| 🔑 **One-click OAuth** | Real OAuth for 15+ of the big ones (GitHub, Google, Slack, Notion, Linear, Microsoft, HubSpot, Asana, Discord, Dropbox, Box, Calendly, Zoom, DocuSign, LinkedIn). Click *Connect*, approve, done — no API keys, no pasted tokens. |
| 📡 **Triggers everywhere** | Webhooks, polling, app events, cron schedules, and manual triggers. Beat survives restarts. |
| 🧠 **Knowledge base (RAG)** | First-class Postgres + pgvector store for retrieval-augmented agents. |
| 👥 **Multi-tenant workspaces** | Invite teammates by email, per-workspace credentials, role-based access. |
| 🎨 **6 color schemes** | Linear / Slate (default) / Indigo / Emerald / Ember / Plum. Pick from Settings → Appearance. |
| 🔁 **Run history & replay** | Every run is logged with inputs, outputs, timing, and the exact payload at each step. Replay any past run with one click. |
| 📨 **Production-grade auth** | JWT sessions, Argon2 password hashing, password-reset emails, and Google OAuth sign-in. |
| 🐳 **Single-host Docker stack** | 7 services (web, api, worker, beat, db, redis, backup) on one VPS. Caddy handles HTTPS. |
| 🚀 **Hardened CI/CD** | GitHub Actions matrix builds → ghcr.io with SBOM + provenance attestations + Trivy scans, auto-deploy over SSH on every `main` push. |

<br />

## 📸 Showcase

> Marketing site (anonymous): **[runmycrew.com](https://runmycrew.com)**
> Product app (authenticated): **[app.runmycrew.com](https://app.runmycrew.com)**

The product features an editorial-grade Linear-style dark UI with 6 colour schemes, custom illustration sets for the marketing pages, an interactive dashboard mockup in the hero, and a fully animated workflow editor.

<br />

## 🏗 Architecture

A single-host stack that fits on a 2 GB VPS, but every layer scales horizontally when you outgrow it.

- **Caddy** terminates HTTPS (auto Let's Encrypt) and reverse-proxies: `/api/*` and `/ws/*` → the API, everything else → the product web app, and `runmycrew.com` → the marketing site.
- **API** (FastAPI) handles HTTP + WebSockets and talks to Postgres, Redis, LLM providers, and OAuth apps.
- **Worker** (Celery) runs every workflow/agent execution off a Redis queue; **Beat** fires schedules and polling triggers. Neither has to be up for the API to serve.
- **Postgres** (+ pgvector) is the single source of truth; **Redis** is broker + cache + pub/sub for live run streaming. A nightly `pg_dump` container keeps backups.

**Layered backend** keeps the code easy to reason about:

```
Router  ─►  Service  ─►  Repository  ─►  Model
(HTTP)      (Logic)       (DB queries)    (SQLAlchemy)
```

Logic lives in services. Routers only wire HTTP. Repositories only do DB queries. No business logic in models, no ORM in routers.

<br />

## 🧰 Tech Stack

<table>
<tr>
<th align="left">Layer</th>
<th align="left">Tools</th>
</tr>
<tr>
<td><strong>Frontend (product)</strong></td>
<td>React 19 · Vite · TypeScript · Tailwind 4 · React Flow · TanStack Query · Zustand</td>
</tr>
<tr>
<td><strong>Frontend (marketing)</strong></td>
<td>Next.js 16 (App Router, standalone) · Tailwind 4 · shadcn/ui · Inter + JetBrains Mono</td>
</tr>
<tr>
<td><strong>Backend</strong></td>
<td>FastAPI · Pydantic 2 · SQLAlchemy · Alembic · uv · Argon2 · python-jose · Anthropic SDK</td>
</tr>
<tr>
<td><strong>Worker</strong></td>
<td>Celery · Celery Beat · Redis broker · structlog</td>
</tr>
<tr>
<td><strong>Data</strong></td>
<td>PostgreSQL 15 · pgvector · Redis 7 (AOF) · nightly <code>pg_dump</code></td>
</tr>
<tr>
<td><strong>Infra</strong></td>
<td>Docker Compose · Caddy 2 (auto-HTTPS / Let's Encrypt) · GitHub Actions · ghcr.io · Trivy · Sigstore (provenance + SBOM)</td>
</tr>
<tr>
<td><strong>Observability</strong></td>
<td>Sentry (frontend) · structured JSON logs · per-step run payload viewer</td>
</tr>
</table>

<br />

## 🚀 Quick Start (self-host)

The fastest way to run the whole stack on a fresh VPS. Two commands plus a `.env`.

### Requirements

- A Linux host (Ubuntu 22.04+ recommended) with Docker 24+ and Docker Compose v2
- A domain pointed at the host (DNS A records for `runmycrew.<your-domain>` and `app.runmycrew.<your-domain>`)
- Ports `80` and `443` reachable from the internet (Caddy needs them for Let's Encrypt)
- ~2 GB RAM minimum (4 GB recommended once you scale to real LLM workloads)

### Steps

```bash
# 1. Clone
git clone https://github.com/bibektimilsina00/runmycrew.git
cd runmycrew

# 2. Configure
cp deploy/.env.production.example deploy/.env
$EDITOR deploy/.env               # fill in secrets, see Environment reference

# 3. Bootstrap once (installs docker, ufw, deploy keys)
sudo bash deploy/bootstrap-vps.sh

# 4. Run the stack
cd deploy
docker compose -f docker-compose.production.yml up -d

# 5. Verify
curl -sS https://app.runmycrew.your-domain.com/health
```

Caddy will issue a Let's Encrypt cert on first request — no certbot setup needed.

### What runs

| Service | Image | Purpose |
|---|---|---|
| `web` | `ghcr.io/<owner>/runmycrew-web` | Caddy + static React SPA (the dashboard) |
| `site` | `ghcr.io/<owner>/runmycrew-site` | Next.js marketing site |
| `api` | `ghcr.io/<owner>/runmycrew-api` | FastAPI app, Alembic migrations on boot |
| `worker` | `ghcr.io/<owner>/runmycrew-worker` | Celery worker (2 concurrency by default) |
| `beat` | `ghcr.io/<owner>/runmycrew-worker` | Celery beat — polling triggers, schedules |
| `db` | `pgvector/pgvector:pg15` | PostgreSQL + pgvector |
| `redis` | `redis:7-alpine` | Celery broker / result backend / cache |
| `backup` | `postgres:15-alpine` | Nightly `pg_dump` with 14-day retention |

Resource caps are tuned for a 2 GB VPS. Bump them in `docker-compose.production.yml` when you upgrade.

<br />

## 🛠 Development setup

For working on RunMyCrew itself.

### Prerequisites

- Node.js 22+ and **pnpm 11+** (via [corepack](https://nodejs.org/api/corepack.html): `corepack enable`)
- Python 3.13 and **uv** (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- PostgreSQL 15 + pgvector locally **or** `docker run pgvector/pgvector:pg15`
- Redis 7 locally **or** `docker run redis:7-alpine`

### Install

```bash
git clone https://github.com/bibektimilsina00/runmycrew.git
cd runmycrew

# JS workspace install (web + site)
pnpm install

# Python install (api + worker)
uv sync
```

### Configure

```bash
# Backend
cp apps/api/.env.example apps/api/.env
$EDITOR apps/api/.env

# Frontend (Vite reads .env from apps/web)
cp apps/web/.env.example apps/web/.env
```

Minimum required env vars are documented in `docs/secrets.md` — at a minimum you need `SECRET_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL`, `REDIS_URL`, and at least one LLM API key (`ANTHROPIC_API_KEY` for Crew AI).

### Run

```bash
# Backend (terminal 1)
uv run --no-sync alembic -c apps/api/alembic.ini upgrade head
uv run --no-sync uvicorn apps.api.app.main:app --reload --port 8000

# Celery worker (terminal 2)
# NB: the worker has NO hot reload — unlike uvicorn --reload, it does not
# pick up backend changes. After editing anything the worker runs (node
# logic, tasks.py, the engine), RESTART this process or you'll test stale
# code and chase phantom bugs.
uv run --no-sync celery -A apps.worker.app.jobs.tasks worker --loglevel=info --concurrency=2

# Celery beat (terminal 3)
uv run --no-sync celery -A apps.worker.app.jobs.tasks beat --loglevel=info

# Frontend product app (terminal 4)
pnpm --filter runmycrew-web dev          # http://localhost:5173

# Marketing site (terminal 5, optional)
pnpm --filter runmycrew-site dev          # http://localhost:3100
```

### Tooling

```bash
# Type-check + lint + format
pnpm --filter runmycrew-web typecheck
pnpm --filter runmycrew-web lint
pnpm --filter runmycrew-site typecheck
uv run ruff check
uv run ruff format

# Migrations
uv run --no-sync alembic -c apps/api/alembic.ini revision --autogenerate -m "describe change"
uv run --no-sync alembic -c apps/api/alembic.ini upgrade head

# Tests
uv run --no-sync pytest apps/api
```

<br />

## 📁 Project structure

```
runmycrew/
├── apps/
│   ├── api/                       FastAPI backend
│   │   └── app/
│   │       ├── core/              config, db, logging, base service
│   │       ├── features/          one folder per domain (auth, workflows, …)
│   │       │   └── <feature>/
│   │       │       ├── models.py        SQLAlchemy
│   │       │       ├── schemas.py       Pydantic
│   │       │       ├── repository.py    DB queries
│   │       │       ├── service.py       business logic
│   │       │       └── router.py        HTTP routes
│   │       ├── credential_manager/  shared infra (OAuth + secrets vault)
│   │       ├── node_system/         pluggable workflow nodes
│   │       └── utils/               email, http, etc.
│   │
│   ├── worker/                    Celery worker + beat
│   │
│   ├── web/                       React SPA (the product)
│   │   └── src/
│   │       ├── App.tsx
│   │       ├── index.css          design tokens + 6 color schemes
│   │       ├── stores/
│   │       ├── features/          mirror of api/features
│   │       │   ├── auth/
│   │       │   ├── dashboard/
│   │       │   ├── workflow-editor/
│   │       │   └── …
│   │       └── shared/            cross-feature UI, layouts, hooks
│   │
│   └── site/                      Next.js marketing site
│       └── src/
│           ├── app/                 routes
│           ├── components/ui/       shadcn primitives
│           ├── features/
│           │   ├── marketing/       Hero, FeatureSection, mockups, …
│           │   ├── docs/
│           │   ├── blog/
│           │   ├── templates/
│           │   ├── integrations/
│           │   └── pricing/
│           └── shared/
│
├── deploy/                        production compose + scripts
│   ├── docker-compose.production.yml
│   ├── bootstrap-vps.sh           one-shot host setup
│   ├── deploy.sh                  pull + up + prune
│   ├── backup.sh / restore.sh
│   └── pg-init/                   `CREATE EXTENSION vector;` on first boot
│
├── docs/                          devops + secrets reference
├── .github/workflows/             build-publish + deploy
└── pnpm-workspace.yaml            JS workspace map
```

<br />

## 🔌 Integrations

Every integration uses our shared **OAuth + credential vault** — encrypted at rest, refreshed automatically, health-checked on every poll.

<table>
<tr>
<th align="left">Category</th>
<th align="left">Providers</th>
</tr>
<tr><td>Communication</td><td>Slack · Gmail · Google Chat</td></tr>
<tr><td>Developer</td><td>GitHub · Linear · Jira</td></tr>
<tr><td>Productivity</td><td>Notion · Google Docs · Sheets · Slides · Calendar · People · YouTube</td></tr>
<tr><td>Marketing</td><td>Meta (Ads + Lead Forms) · Google Search Console · GA4</td></tr>
<tr><td>Finance</td><td>Stripe</td></tr>
<tr><td>Storage</td><td>Google Drive · Google Cloud Storage</td></tr>
<tr><td>AI</td><td>Anthropic Claude · OpenAI GPT</td></tr>
</table>

Adding a new connector is a single skill scaffold: `/new-integration` generates the credential provider, HTTP client, service layer, `loadOptions` endpoints, and node wiring in one pass.

<br />

## 🎨 Theming

Six fully-baked colour schemes ship out of the box. Every UI surface uses CSS custom properties so changing the scheme retints the entire app instantly — no rebuild needed.

| Scheme | Surface tone | Accent |
|---|---|---|
| **Slate** *(default)* | `#121316` lifted near-black | `#6b76e0` |
| **Linear** | `#0f1011` Linear's near-pure-black | `#5e6ad2` |
| **Indigo** | `#0c0d12` blue-tinted dark | `#7c83ff` |
| **Emerald** | `#0a0d0b` green-tinted dark | `#3fb98a` |
| **Ember** | `#0d0a09` warm dark | `#e0673f` |
| **Plum** | `#0c0a0e` purple-tinted dark | `#a06cf0` |

Switch from **Settings → Appearance**, persists in `localStorage`, applies via a single `<html data-theme="…">` attribute. Adding a new scheme is one CSS block in `apps/web/src/index.css`.

<br />

## 🚢 Deployment

### CI/CD pipeline

Every push to `main` triggers:

```
┌─────────────────────────────────────────────────────────────────┐
│                       build-publish                              │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  build   │  │  build   │  │  build   │  │  build   │         │
│  │   api    │  │  worker  │  │   web    │  │   site   │ ◀── matrix
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │             │             │             │                │
│       └─────────────┴──────┬──────┴─────────────┘                │
│                            │                                     │
│              ┌─────────────▼─────────────┐                       │
│              │   ghcr.io                  │                       │
│              │   tags: latest, sha-<7>    │                       │
│              │   + SBOM + provenance      │                       │
│              └─────────────┬─────────────┘                       │
│                            │                                     │
│                  ┌─────────▼─────────┐                           │
│                  │  Trivy scan       │                           │
│                  │  (CRITICAL/HIGH)  │                           │
│                  └───────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                          deploy                                  │
│                                                                  │
│  ssh → scp compose + scripts → docker compose pull + up + prune │
│       → smoke-test both hostnames → notify                       │
└─────────────────────────────────────────────────────────────────┘
```

Sigstore-signed provenance + SBOM ship inside every image manifest, so consumers see them via `docker pull`. Trivy SARIF lands in the GitHub Security tab.

### Tag pinning

Set `RUNMYCREW_IMAGE_TAG=sha-abc1234` in `deploy/.env` to roll back without touching the compose file.

### Backups

The `backup` service runs `pg_dump` nightly into a named volume with 14-day retention. Restore with `bash deploy/restore.sh <dump-file>`.

### Operator runbook

Everyday operations + incident playbooks live in [`docs/deploy.md`](docs/deploy.md).

<br />

## 🔐 Security

- **At rest:** OAuth credentials encrypted with `ENCRYPTION_KEY` (Fernet). Rotating the key would invalidate every stored credential — do not rotate without a migration plan.
- **In transit:** Caddy terminates TLS via Let's Encrypt, HSTS preload, strict CSP-friendly response headers.
- **Auth:** Argon2 password hashing, JWT with `SECRET_KEY`, password-reset tokens carry a typed claim and expire in 15 minutes.
- **Container hardening:** SBOM + Sigstore provenance attached to every image, Trivy scans on every push (CRITICAL/HIGH severities surfaced to the GitHub Security tab).
- **Infrastructure:** `ufw` rules limit inbound to 22/80/443, non-root users in every container (uid 10001).
- **Supply chain:** Dependabot for npm + Docker + uv lockfiles, automatic monthly cadence.

See [`docs/secrets.md`](docs/secrets.md) for the full secret inventory and rotation impact per key.

<br />

## 🤝 Contributing

PRs welcome! A few conventions to match the existing code:

- **Backend layering is strict.** Logic in services, queries in repositories, HTTP in routers. No business logic in models.
- **Frontend is feature-modular.** `features/<thing>/` owns its UI + state. Shared primitives live in `shared/`.
- **Never use `as any`, `# type: ignore`, `@ts-ignore`.** Diagnose the actual cause, fix it upstream. The full convention list lives in [`CLAUDE.md`](CLAUDE.md).
- **Run `pnpm --filter runmycrew-web typecheck && uv run ruff check`** before opening a PR.
- **Conventional Commits** for commit messages (`feat:`, `fix:`, `chore:`, …).

For larger changes please open an issue first so we can align on scope.

<br />

## 📜 License

[MIT](LICENSE) © Bibek Timilsina — feel free to fork, deploy, and adapt. Attribution appreciated but not required.

<br />

---

<div align="center">

<sub>Built with ⚡ in Nepal · Powered by Claude</sub>

</div>
