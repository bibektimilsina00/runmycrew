# Phase 5 — Reliability & Ops (2–3 days)

No backup = not production. This phase is mostly human-owned infrastructure work; Claude drafts the scripts and runbooks.

## 1. Backups (human)

- [ ] Nightly cron on the VPS: `pg_dump | gzip` → off-VPS storage (object storage or even rclone to Drive). 14-day retention.
- [ ] **Restore drill — actually do it once:** restore last night's dump into a scratch database, run the API against it, log in. Write the exact commands into the runbook while doing it. An unrestored backup is a hope, not a backup.

## 2. Rollback drill (human + Claude)

- [ ] Images are tagged `:sha-<short>` — practice one full rollback: pin the previous SHA in compose on the VPS, `docker compose up -d`, smoke test, roll forward again. Time it.
- [ ] Write `docs/production-hardening/RUNBOOK.md` section "Rollback" with the exact commands used.
- [ ] Migration caveat in the runbook: rolling back past a migration requires the migration's `downgrade()` — we keep those working (e.g. named FK constraints); note which releases carry migrations.

## 3. Error tracking (human creates projects, Claude wires)

- [ ] Sentry (or GlitchTip) project for **api** and **worker** — the whole July theme was silent worker failures visible only in a terminal. `sentry-sdk` with FastAPI + Celery integrations, DSN via env.
- [ ] Frontend Sentry exists — confirm DSN is current and releases are tagged with the git SHA so errors map to deploys.
- [ ] Force one test error through each of the three (api route, worker task, frontend) and see it arrive. Not wired until proven.

## 4. Monitoring & health (human signs up, Claude scripts)

- [ ] Uptime checks: marketing site, app shell, API health endpoint.
- [ ] One **synthetic hosted-chat probe** every 5 min: create session + send message against a dedicated probe app; alert on non-200 or timeout. This exercises api + redis + worker + db in one request chain — it's the check that would have caught the stale-worker class in prod.
- [ ] Disk/memory alert on the VPS (node_exporter + hosted Grafana free tier, or the provider's built-in alerts).

## 5. Queue & cache durability

- [ ] Celery: `execute_workflow` gets the same crash-safety `execute_app_message` got — max retries + persisted failure state + terminal event, never a silently vanished run.
- [ ] Confirm Celery task `acks_late`/visibility behavior on worker kill: kill the worker mid-run, verify the execution ends `failed` (not stuck `running` forever) — add a reaper if it doesn't.
- [ ] Redis persistence: decide (and document) whether pub/sub-missed events + 1h snapshots are acceptable loss on restart. If yes, write that down; if no, enable AOF.

## 6. Load smoke (Claude)

- [ ] `k6`/`hey` against the public chat endpoint chain (session + message) at increasing concurrency until p95 > 2s or errors. **Write the number down** in the runbook ("known limit: N concurrent chats on current VPS"). Fixing it is out of scope; knowing it is not.
- [ ] Same for the editor's run endpoint at 10 concurrent runs.

## Done when

- Restore drill performed once, commands in RUNBOOK.md.
- Rollback drill performed once, commands in RUNBOOK.md.
- Test error visible in Sentry from api, worker, and frontend.
- Synthetic chat probe live and alerting.
- Load numbers recorded.
