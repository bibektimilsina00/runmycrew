# RunMyCrew Ops Runbook

Operational procedures for the production VPS. Commands are copy-paste
ready; anything a human must run against prod (drills, error tests) is
marked **(HUMAN)** with the exact commands to run and log.

VPS: `root@139.59.71.226` · compose: `deploy/docker-compose.production.yml`
(referred to below as `$C`). Set `export C=docker-compose.production.yml`
after `cd`-ing into the repo on the VPS.

---

## Deploy chain (reference)

PR squash-merge → `build-publish.yml` builds `:sha-<short>` images (api,
worker, web, site) + Trivy scan (gates on CRITICAL) → `deploy.yml` SSHes to
the VPS and runs `deploy/deploy.sh` → `git pull --ff-only`, `compose pull`,
`compose up -d --remove-orphans`.

The deployed image sha is exposed to containers as `RELEASE`
(`RUNMYCREW_IMAGE_TAG`) → Sentry release, and baked into the web bundle as
`VITE_RELEASE`.

---

## Rollback  **(HUMAN — drill once, then keep for real incidents)**

Images are immutable and tagged `:sha-<short>`. Rollback = pin the previous
sha and re-up. No rebuild.

```bash
ssh root@139.59.71.226
cd /root/runmycrew           # repo checkout on the VPS
export C=deploy/docker-compose.production.yml

# 1. Find the sha to roll back to (previous good deploy).
docker images | grep runmycrew-api        # lists the sha tags present
# …or read it from the merge history: gh run list --workflow deploy

# 2. Pin it and re-up (all services move together).
export RUNMYCREW_IMAGE_TAG=sha-<previous>
docker compose -f "$C" pull
docker compose -f "$C" up -d --remove-orphans

# 3. Smoke test.
curl -fsS https://app.runmycrew.com/healthz && echo OK
curl -fsS https://app.runmycrew.com/api/v1/health | jq .

# 4. Roll forward again when the fix is ready (unset the pin → latest).
unset RUNMYCREW_IMAGE_TAG
docker compose -f "$C" pull && docker compose -f "$C" up -d
```

**Migration caveat:** rolling back the code past a DB migration requires that
migration's `downgrade()`. We keep downgrades working (named FK constraints,
reversible column ops). A release that carries a migration is noted in its PR;
if the rollback target predates a migration you must `alembic downgrade` to the
matching revision **before** starting old containers, or the old code will hit
columns/tables it doesn't expect. Check:

```bash
docker compose -f "$C" exec api sh -lc 'cd apps/api && uv run --no-sync alembic current'
```

**Record after the drill:** time to roll back, time to roll forward.

---

## Restore from backup  **(HUMAN — drill monthly)**

Nightly `backup.sh` runs in the `backup` container: `pg_dump --format=custom`
gzipped to the `pg_backups` volume, 14-day retention, `latest.dump.gz`
symlink. **An unrestored backup is a hope, not a backup — actually do this.**

```bash
ssh root@139.59.71.226
cd /root/runmycrew
export C=deploy/docker-compose.production.yml
BK=/var/lib/docker/volumes/runmycrew_pg_backups/_data

# 1. Verify last night's dump exists and is non-trivial.
ls -la "$BK/latest.dump.gz"

# 2. Restore into a SCRATCH database (never the live one during a drill).
docker compose -f "$C" exec db psql -U runmycrew -c 'CREATE DATABASE restore_drill;'
gunzip -c "$BK/latest.dump.gz" | \
  docker compose -f "$C" exec -T db pg_restore -U runmycrew -d restore_drill --no-owner --no-acl

# 3. Sanity-check row counts against live.
docker compose -f "$C" exec db psql -U runmycrew -d restore_drill \
  -c 'SELECT count(*) FROM "user"; SELECT count(*) FROM workflow;'

# 4. Point the API at the scratch DB and log in (proves the dump is usable):
#    run a throwaway api container with POSTGRES_DB=restore_drill, hit /health,
#    log in through the UI. Then drop the scratch DB.
docker compose -f "$C" exec db psql -U runmycrew -c 'DROP DATABASE restore_drill;'
```

**Off-VPS copy (HUMAN, required):** the dump volume lives on the same VPS as
the DB — a disk loss takes both. Add a nightly `rclone copy` (or `scp`) of
`$BK/latest.dump.gz` to object storage / Drive. Until that exists, a VPS loss
is data loss.

For a real recovery: same steps, restore into the live DB name after stopping
`api`/`worker`/`beat` (leave `db` up), then start them back.

---

## Stuck / abandoned executions

A run stuck `running` should self-heal: the `reap_stale_executions` beat task
(every 2 min) fails any execution `running` past 30 min (dead-worker orphan),
and the worker's crash-net fails runs whose task escaped its handlers. To force
a sweep or inspect:

```bash
# Manually trigger the reaper.
docker compose -f "$C" exec beat sh -lc \
  'cd /app && uv run --no-sync python -c "from apps.worker.app.jobs.tasks import reap_stale_executions as r; r()"'

# Count currently-running executions.
docker compose -f "$C" exec db psql -U runmycrew \
  -c "SELECT count(*) FROM execution WHERE status='running';"
```

If runs legitimately take >30 min, raise `_STALE_EXECUTION_SECONDS` in
`apps/worker/app/jobs/tasks.py`.

---

## Error tracking  **(HUMAN — create projects, then verify)**

Sentry is wired and no-ops until `SENTRY_DSN` is set (api + worker read the
same env; frontend uses `@sentry/react`). Set `SENTRY_DSN` in `deploy/.env`
and redeploy. Releases are tagged with the image sha automatically.

**Verify each of the three actually reports (don't trust untested wiring):**

```bash
# API: hit a route that raises (add a temporary /debug-sentry or trigger a
# known 500), confirm the event lands in the api project.
# Worker: enqueue a task that raises —
docker compose -f "$C" exec beat sh -lc \
  'cd /app && uv run --no-sync python -c "from apps.api.app.core.celery import celery_app; celery_app.send_task(\"reap_stale_executions\")"'
#   (or a purpose-made failing task) and confirm it lands in the worker project.
# Frontend: throw in a component / use the report-bug shortcut, confirm the
#   event carries release=sha-<short>.
```

---

## Redis persistence (decided)

Redis runs with **AOF on** (`--appendonly yes`), so a hard restart keeps
in-flight Celery state and the queue. Pub/sub events in flight at the instant
of a crash are lost, but execution results are persisted in Postgres and the
1-hour Redis snapshot (`execution:{id}:snapshot`) replays for late SSE
subscribers. **Accepted loss on Redis restart:** only the sub-second window of
pub/sub frames mid-broadcast; nothing durable. No action needed.

---

## Load limits  **(HUMAN — run once, record the numbers)**

Scripts in `scripts/load/`. Run from a machine with network access to prod (or
against the e2e stack for a lower bound). **Write the numbers here after the
run** so we know the ceiling before a launch spike hits it.

```bash
# Public hosted-chat chain (session + message) — the api+redis+worker+db path.
k6 run scripts/load/hosted-chat.js -e BASE=https://app.runmycrew.com

# Editor run endpoint at concurrency.
k6 run scripts/load/workflow-run.js -e BASE=https://app.runmycrew.com -e TOKEN=<jwt>
```

**Recorded limits (fill in):**
- Hosted chat: known limit ≈ ___ concurrent chats before p95 > 2s on current VPS.
- Workflow run: ___ concurrent runs before errors.

---

## Incident checklist

Work top to bottom; stop when you've found and addressed the cause.

1. **Probe** — is the app actually down? `curl -fsS https://app.runmycrew.com/healthz`
   and `.../api/v1/health | jq .` (the health payload names which of
   api/db/redis/worker is unhealthy). Run the synthetic probe:
   `BASE=… WS=… SLUG=… scripts/synthetic-chat-probe.sh`.
2. **Sentry** — check the api / worker / frontend projects for a spike; the
   release tag (image sha) points at the deploy that introduced it.
3. **VPS resources** — `ssh root@139.59.71.226 'df -h; free -m'`. Disk full or
   OOM is the usual culprit for a wedged worker.
4. **Containers** — `docker compose -f "$C" ps` — anything not `healthy`?
   `docker compose -f "$C" logs --tail 200 <svc>`.
5. **Worker** — stuck runs self-heal via the reaper (every 2 min, fails runs
   `running` > 30 min). To force: see §"Stuck / abandoned executions".
6. **Rollback decision** — if a recent deploy caused it and no quick fix is
   obvious, roll back (§Rollback) and investigate off the critical path.

---

## Known limits & policies

- **Load ceiling:** _(fill in from `scripts/load/` runs — k6, date)._ Until
  measured, treat as unknown; the scripts are in `scripts/load/`.
- **Redis restart** loses only the sub-second window of pub/sub frames
  mid-broadcast (AOF is on, queue + results persist in Postgres/AOF). Accepted.
- **Celery reliability:** `acks_late=True`; a failed task marks its execution
  terminal (crash-net) and the reaper (2-min beat, 30-min cutoff) catches
  dead-worker orphans. No task auto-retry — a failed run is a failed run, not
  silently re-executed (avoids double side-effects).
- **Auth rate limit:** `RATE_LIMIT_AUTH` (default 5/min per IP). Public-app
  message + unlock have their own Redis sliding-window limits.

---

## Contacts / access

_(fill in — kept out of git if sensitive; store in the team password manager)_

- **VPS:** `root@139.59.71.226` (SSH key: _____).
- **DNS:** registrar _____, records for `runmycrew.com` / `app.` / `www.`.
- **Container registry:** GHCR under the repo owner.
- **Sentry:** org _____, projects `api` / `worker` / `frontend`.
- **Uptime monitor:** _____ (hosts the 5-min synthetic-chat probe).
- **Secrets:** `deploy/.env` on the VPS + the `ENV_PRODUCTION` GitHub secret.
