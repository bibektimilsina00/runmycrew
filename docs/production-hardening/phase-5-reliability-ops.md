# Phase 5 — Reliability & Ops (2–3 days)

> **Status: CODE COMPLETE (2026-07-12), branch `test/phase-5-reliability`.**
> The code-owned reliability work landed; the infra drills are human-owned
> and scripted in `RUNBOOK.md`. Done in code: `execute_workflow` +
> `execute_crew` get a crash-net (mark terminal-failed + emit event so a
> setup crash can't leave a run stuck `running` and falsely-ack the Celery
> message), plus a `reap_stale_executions` beat task every 2 min for
> dead-worker (SIGKILL) orphans — both idempotent, +3 tests (suite 921→924).
> Sentry release wiring completed (backend `RELEASE` env from the image
> sha, frontend `VITE_RELEASE` build-arg). `RUNBOOK.md` written with
> rollback / restore / reaper / Sentry-verify / Redis-persistence /
> load-limit sections. Synthetic chat probe (`scripts/synthetic-chat-probe.sh`)
> and k6 load scripts (`scripts/load/`) drafted. Backup/restore scripts
> already existed (nightly custom-format dump, 14-day retention, AOF on).
> **HUMAN-OWNED, still open:** run the restore + rollback drills once and
> record the numbers; add the off-VPS backup copy; create the Sentry
> projects + set `SENTRY_DSN`; wire the probe into an uptime monitor; run
> the load scripts and record the ceiling. Each has copy-paste commands in
> RUNBOOK.md.

No backup = not production. This phase is mostly human-owned infrastructure work; Claude drafts the scripts and runbooks.

## 1. Backups (human)

- [x] Nightly dump scripted (`deploy/backup.sh`, custom format, 14-day retention). **HUMAN:** off-VPS copy still needed — `pg_dump | gzip` → off-VPS storage (object storage or even rclone to Drive). 14-day retention.
- [ ] **(HUMAN) Restore drill — actually do it once:** commands in RUNBOOK.md §Restore — restore last night's dump into a scratch database, run the API against it, log in. Write the exact commands into the runbook while doing it. An unrestored backup is a hope, not a backup.

## 2. Rollback drill (human + Claude)

- [ ] **(HUMAN)** Images are tagged `:sha-<short>` — practice one full rollback: pin the previous SHA in compose on the VPS, `docker compose up -d`, smoke test, roll forward again. Time it.
- [x] Wrote `docs/production-hardening/RUNBOOK.md` section "Rollback" with the exact commands used.
- [x] Migration caveat in the runbook: rolling back past a migration requires the migration's `downgrade()` — we keep those working (e.g. named FK constraints); note which releases carry migrations.

## 3. Error tracking (human creates projects, Claude wires)

- [x] `sentry-sdk` wired for api + worker (no-op until DSN set), release=image sha. **HUMAN:** create the projects + set `SENTRY_DSN`. Was — — the whole July theme was silent worker failures visible only in a terminal. `sentry-sdk` with FastAPI + Celery integrations, DSN via env.
- [x] Frontend Sentry release now baked from `VITE_RELEASE` (image sha). **HUMAN:** confirm DSN is current and releases are tagged with the git SHA so errors map to deploys.
- [ ] **(HUMAN)** Force one test error through each of the three (api route, worker task, frontend) and see it arrive. Not wired until proven.

## 4. Monitoring & health (human signs up, Claude scripts)

- [ ] **(HUMAN)** Uptime checks: marketing site, app shell, API health endpoint.
- [x] Synthetic hosted-chat probe scripted (`scripts/synthetic-chat-probe.sh`). **HUMAN:** wire into a 5-min uptime monitor. Was — every 5 min: create session + send message against a dedicated probe app; alert on non-200 or timeout. This exercises api + redis + worker + db in one request chain — it's the check that would have caught the stale-worker class in prod.
- [ ] **(HUMAN)** Disk/memory alert on the VPS (node_exporter + hosted Grafana free tier, or the provider's built-in alerts).

## 5. Queue & cache durability

- [x] Celery: `execute_workflow` + `execute_crew` got the same crash-safety `execute_app_message` got — max retries + persisted failure state + terminal event, never a silently vanished run.
- [x] Confirmed `acks_late` behavior; added `reap_stale_executions` reaper for worker-kill orphans (was the gap — a swallowed outer exception falsely-acked). Original:/visibility behavior on worker kill: kill the worker mid-run, verify the execution ends `failed` (not stuck `running` forever) — add a reaper if it doesn't.
- [x] Redis persistence decided + documented (AOF on; RUNBOOK §Redis). Original: (and document) whether pub/sub-missed events + 1h snapshots are acceptable loss on restart. If yes, write that down; if no, enable AOF.

## 6. Load smoke (Claude)

- [x] k6 script written (`scripts/load/hosted-chat.js`). **HUMAN:** run + record. Original: endpoint chain (session + message) at increasing concurrency until p95 > 2s or errors. **Write the number down** in the runbook ("known limit: N concurrent chats on current VPS"). Fixing it is out of scope; knowing it is not.
- [x] k6 script written (`scripts/load/workflow-run.js`). **HUMAN:** run + record. Original: at 10 concurrent runs.

## Done when

- Restore drill performed once, commands in RUNBOOK.md.
- Rollback drill performed once, commands in RUNBOOK.md.
- Test error visible in Sentry from api, worker, and frontend.
- Synthetic chat probe live and alerting.
- Load numbers recorded.
