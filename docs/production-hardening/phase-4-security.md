# Phase 4 — Security Pass (2 days)

The hosted chat/form pages made the platform publicly reachable. This phase is no longer optional.

## 1. Structured review

- [ ] Run the `/security-review` skill over the branch; triage every finding to a board card. Priority order:
  1. `apps/api/app/features/apps/` — the anonymous public surface (session cookies, unlock flow, uploads).
  2. Auth (`features/auth`) — JWT lifetime, reset flow, OAuth callbacks.
  3. WebSockets — token rides the query string: confirm access logs don't capture full WS URLs (uvicorn + any proxy), or move to first-message auth.
  4. Template publish/install — credential scrubbing (test exists; re-verify camelCase variants).

## 2. Public-app abuse hardening (verify, don't assume)

- [ ] Rate limit actually returns 429: loop `POST /message` past `rate_limit_per_min`, assert 429 + `Retry-After`.
- [ ] Session cost cap trips at 402; daily cap trips; both covered by tests with a fake usage recorder.
- [ ] Uploads: oversize ⇒ 4xx; disallowed MIME ⇒ 403; filename with `../` stored safely; upload disabled by default respected.
- [ ] Hosted resolution can't leak: inactive graphs 404; other workspaces' slugs 404.
- [ ] Anonymous sessions: cookie is httpOnly + path-scoped (it is — assert in a test so it stays).

## 3. Tenant isolation test file (`apps/api/tests/test_tenant_isolation.py`)

- [ ] Two users, two workspaces. Parametrized over every authenticated router (workflows, crews, executions, credentials, templates/mine, skills, personas, app sessions/owner endpoints): user B gets 403/404 on every one of user A's object ids. One file, table-driven — new routers must be added or the test fails on route-count drift.

## 4. Secrets hygiene

- [ ] `grep -ri "api_key\|secret\|token" apps/api/app --include="*.py" | grep -i "logger\|print"` → nothing logs secret values.
- [ ] Credentials encrypted at rest — confirm the credential_manager path and where the key lives on the VPS (not in the repo, not in the image).
- [ ] `deploy/.env` handling: only via the `ENV_PRODUCTION` GitHub secret; confirm no `.env` committed anywhere (`git log --all --diff-filter=A -- "*.env"`).
- [ ] Rotate anything the review flags. (Human task.)

## 5. Dependency + image scanning

- [ ] `pip-audit` (api/worker) and `npm audit --audit-level=high` (web) as CI steps; triage current output to zero high/critical.
- [ ] Trivy already scans images on publish — confirm it's still failing the workflow on CRITICAL (it is configured to; verify a run).

## Done when

- Security-review criticals: zero open.
- Isolation test file merged and green.
- Abuse tests (429/402/upload) merged and green.
- Secrets grep clean; rotation done where flagged.
