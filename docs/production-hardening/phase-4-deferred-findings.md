# Phase 4 — deferred security findings (carded, not yet fixed)

The surgical, low-regression fixes landed in the phase-4 PR. These are the
architectural ones that need a design decision or a bigger change — each is
real, none is a drop-everything emergency (exploitability noted).

## 1. Public-app cost/rate caps are bypassable (HIGH) — FIXED 2026-07-13

> **FIXED (branch `fix/public-app-spend-cap`).** Daily cap now reads an
> app-level Redis counter (`app_spend:{source}:{date}`) the worker
> increments with real cost after each run — keyed on the workflow/crew
> id, so rotating the session cookie can't reset it. The effective cap is
> the owner's `daily_cost_cap_usd` when set, else a non-zero config
> default (`PUBLIC_APP_DEFAULT_DAILY_CAP_USD=25`), closing the
> unconfigured-app hole. A per-app in-flight counter
> (`PUBLIC_APP_MAX_INFLIGHT=6`) bounds the concurrent-burst race the
> post-hoc cost record couldn't. Runtime-verified against the e2e stack:
> a fresh session cookie over the counter still 402s. +7 tests. The
> remaining note below is the original finding.

Per-session rate limit + `session_cost_cap_usd` key on `session.id`, but an
anonymous client mints a fresh session per request (`POST /session`), so
rotating the cookie resets the window and the session cap to zero. Cost is
also written back only *after* the run (`tasks.py`), so concurrent messages
all pass the cap check before any spend records. `daily_cost_cap_usd`
defaults to 0 (disabled).
**Fix:** atomic Redis spend counter incremented *at dispatch* (not summed
from lagging rows); per-app global window keyed on the (now-trustworthy) IP,
not per-session; non-zero default daily cap; cap concurrent in-flight
executions per app.
**Exploitable now?** Yes for cost, if an app has no daily cap set. The XFF
leftmost-spoof half is already closed (rightmost hop). The session-rotation
half remains.

## 2. Upload storage: base64 data-URLs in Postgres (HIGH) — PARTIALLY FIXED 2026-07-13

> **HARDENED (branch `fix/upload-quota-v2`).** Two of the three exploitable
> pieces are closed in code: a per-session upload quota (count 20 / 50 MB,
> config-tunable) bounds the DB-bloat DoS, and magic-byte sniffing rejects
> active markup (svg/html/xml/script) whose bytes betray a spoofed
> content_type. The remaining piece — moving blobs OFF the primary DB to
> object storage served from a sandboxed domain — needs infra and stays
> carded (human). The original finding follows.

Uploads are base64-inflated and stored in an `AppFile.url` TEXT column, no
per-session/app quota, served back inline as `data:` URLs. Active-content
MIMEs (svg/html/js) are now blocked and size is precapped, but the storage
model itself is wrong.
**Fix:** off-DB blob storage (object store), served from a sandboxed domain
with `Content-Disposition: attachment` and a restrictive CSP; magic-byte
content sniffing instead of trusting `content_type`; per-session byte + count
quota.
**Exploitable now?** DB-bloat DoS still possible via many in-quota uploads.

## 3. WebSocket token in query string (LOW)
`/ws/executions/{id}?token=<jwt>` — the JWT can land in proxy/access logs.
**Fix:** move to first-message auth or an `Authorization` header on the
upgrade (frontend refactor). **Exploitable now?** Only with log access;
mitigated by token expiry.

## 4. Unlock token is a deterministic hash (LOW)
`_unlock_token_for = sha256(workflow_id:password_hash)` — same for all
visitors, rotates only on password change. Unforgeable without the argon2
hash (never exported), but the wrong shape.
**Fix:** random opaque per-issue token stored server-side (Redis, TTL),
validated on each gated request.

## 5. `daily_cost_cap` query loads all sessions (LOW, perf)
`SELECT * FROM app_session WHERE …` summed in Python on each capped message.
**Fix:** `SELECT sum(total_cost_usd)` or the Redis counter from #1.

## 6. pip-audit is report-only
Backend `pip-audit` runs `|| true` in CI. Triage the current Python advisory
backlog to zero, then make it blocking (drop the `|| true`).

---
Frontend `pnpm audit --prod --audit-level=high` is already **blocking** and
green; the one design-time-only jsonata advisory is allowlisted with
justification in `pnpm-workspace.yaml`.
