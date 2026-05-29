# Architecture

Fuse is a workflow-automation / AI-agent platform: users build node graphs on a
canvas and run them. This document reflects the **current, verified** structure
of the codebase.

## Monorepo

| App | Stack | Role |
|---|---|---|
| `apps/api` | FastAPI + SQLModel | HTTP API, auth, persistence, execution dispatch |
| `apps/worker` | Celery | Async workflow execution (the runtime) |
| `apps/web` | Vite + React 19 | Canvas editor + dashboard (Zustand, TanStack Query, ReactFlow) |

Tooling: **pnpm + Turborepo** (JS), **uv workspace** (Python). Infra: **PostgreSQL
(pgvector)** + **Redis** (Celery broker *and* realtime pub/sub). Local infra via
`docker compose up -d db redis` (`make db-up`).

## Backend layout (`apps/api/app`)

The API is organized **feature-first**. HTTP routes are aggregated in
`api/v1/router.py`, which mounts one router per feature from `features/*`.

```
features/<feature>/
  models.py       # SQLModel tables
  schemas.py      # Pydantic request/response contracts
  repository.py   # DB queries only
  router.py       # HTTP wiring only
  service.py      # business logic (Router → Service → Repository → Model)
```

Cross-cutting modules live at the top level (siblings, not features):

- `core/` — config, database, redis, celery, logger, security, http
- `credential_manager/` — **shared infrastructure**: AES encryption, vault,
  OAuth flows, API-key/provider resolution. Used by API features, the node
  execution path, *and* the worker. **Do not move this into `features/`** — it
  is consumed across layers/apps by design.
- `integrations/` — external service clients (slack, github, notion, …)
- `node_system/` — node base classes, registry (auto-discovery), the node
  implementations (`nodes/<category>/…`), validation, templates
- `execution_engine/` — the orchestration entry (`engine/`) used by the API to
  dispatch runs

## Frontend layout (`apps/web/src`)

Feature-first as well: `features/<feature>/{components,hooks,pages,services,
stores,types}`. Shared UI in `shared/`. API access goes through
`shared/utils/apiClient.ts::requestJson`, which validates every response against
a Zod schema and returns the schema's **output** type.

## Data

SQLModel models per feature; Alembic migrations in `apps/api/alembic/versions`.
`make migrate` applies them; CI runs `alembic upgrade head` + `alembic check`
(model-drift gate).

## Known incomplete areas (be honest with yourself)

- **Empty scaffolding:** several subsystems are placeholder files with no
  implementation (parts of `worker/app/{execution,sandbox}`, and
  `execution_engine/{state,events,queue,workers,sandbox,logs}`). The live engine
  is `execution_engine/engine/` + `worker/app/jobs/tasks.py` + the
  `node_system` runner — see [execution-flow.md](./execution-flow.md).
- **`logic.condition` evaluator is a stub** — only literal `true`/`false`
  evaluate; real expressions silently never match.
- **CodeNode sandbox is phase A** (process isolation + resource limits), not full
  network/filesystem isolation. See [execution-flow.md](./execution-flow.md).

## Conventions

See `AGENTS.md` for naming, imports (absolute only), logging, and styling rules.
Note: parts of `AGENTS.md` predate the current layout (e.g. it references a
`packages/` directory that does not exist) — this document is authoritative for
structure.
