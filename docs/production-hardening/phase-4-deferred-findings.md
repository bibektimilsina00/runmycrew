# Phase 4 — deferred security findings (fully triaged 2026-07-13)

> **All items resolved.** #1 cost-cap (HIGH) and #2 upload hardening (HIGH,
> the code-ownable pieces) FIXED; #3 WS-token (LOW) FIXED; #4 unlock token
> (LOW) assessed WON'T-FIX with rationale; #5 daily-cap query (LOW perf)
> mooted — #1 replaced that query with the Redis counter. The only work
> still open is the off-DB upload blob storage (needs object-storage
> infra, human-owned) noted under #2.

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

## 3. WebSocket token in query string (LOW) — FIXED 2026-07-13

> **FIXED (branch `fix/ws-subprotocol-auth`).** All four WS clients
> (execution stream, workspace runs, collaboration ×2 URL builders) now
> pass the JWT as a `Sec-WebSocket-Protocol` subprotocol (`["fuse-auth",
> "<jwt>"]`) instead of `?token=`, so it no longer lands in proxy/uvicorn
> access logs or history. Backend reads it via `core/ws_auth.py` and
> echoes `fuse-auth` on accept; the query param is still accepted as a
> fallback for older clients. Runtime-verified end-to-end through
> Caddy→uvicorn: streaming specs pass and the WS URL carries no token.
> +6 tests. Original finding follows.

`/ws/executions/{id}?token=<jwt>` — the JWT can land in proxy/access logs.
**Fix:** move to first-message auth or an `Authorization` header on the
upgrade (frontend refactor). **Exploitable now?** Only with log access;
mitigated by token expiry.

## 4. Unlock token is a deterministic hash (LOW) — WON'T FIX (assessed 2026-07-13)

`_unlock_token_for = sha256(workflow_id:password_hash)` — same for all
visitors, rotates only on password change. Unforgeable without the argon2
hash (never exported), flagged originally as "the wrong shape."

> **Decision: keep as-is.** On review the current design is not just
> non-exploitable — it has two properties the proposed random-token
> rewrite would LOSE:
> 1. **Auto-invalidates on password change.** The token is a function of
>    `password_hash`, so changing the app password changes the token and
>    every existing unlock cookie is instantly rejected — exactly what an
>    owner rotating a leaked password wants. A random Redis token would
>    survive a password change until its TTL unless we also key it on the
>    hash, at which point we've reinvented the hash dependency.
> 2. **No Redis dependency on the gate.** Validation is a pure string
>    compare, so a password-gated app keeps working during a Redis outage.
>    A Redis-backed token must fail closed on outage → gated apps become
>    unreachable, trading a non-issue for an availability regression.
>
> The only thing the random token buys is per-visitor revocation, which
> isn't a stated requirement (a visitor who shares their unlock cookie
> could equally share the password). Not worth the regressions. If
> per-visitor revocation is ever needed, revisit — but as a feature, not a
> security fix.

## 5. `daily_cost_cap` query loads all sessions (LOW, perf) — MOOTED 2026-07-13
`SELECT * FROM app_session WHERE …` summed in Python on each capped message.
**Resolved by #1:** the per-app Redis spend counter replaced this query
entirely — the daily cap no longer touches the session table.

## 6. pip-audit is report-only
Backend `pip-audit` runs `|| true` in CI. Triage the current Python advisory
backlog to zero, then make it blocking (drop the `|| true`).

---
Frontend `pnpm audit --prod --audit-level=high` is already **blocking** and
green; the one design-time-only jsonata advisory is allowlisted with
justification in `pnpm-workspace.yaml`.
