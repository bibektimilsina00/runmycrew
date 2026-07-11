# Production Hardening Plan

**Goal:** no new features. Make what exists solid, tested end-to-end, and production ready.

**Rule:** work the phases in order. Phases 1–3 build the safety net that makes 4–6 fast and safe. Every finding becomes a card on the hardening board before it gets fixed — that's how we know when we're done.

## Why these phases (evidence)

Every phase targets a failure class that actually shipped and was caught in July 2026:

| Shipped bug | Root class | Phase |
|---|---|---|
| 28 of 36 polling triggers silently unregistered | `except: pass` swallow | 1 |
| Every L1 verification assertion passed unconditionally | untested truthy fallback | 1 |
| Crew swallowed round failures → "No response produced." | error not propagated | 1 |
| `$json.path` never resolved in the shipped Verify/Reviewer presets | untested template syntax | 1 |
| Chat replies duplicated / vanished (StrictMode double-invoke) | zero frontend tests | 2 |
| Crew sessions crashed the chat page (`workflow_id: null` vs zod) | backend/frontend schema drift | 2 |
| Editor never attached to chat runs (`activeExecutionId` unset) | untested state plumbing | 2 |
| Every one of the above found by *manual* Playwright runs | no automated E2E | 3 |
| Public chat/form pages now exist, unreviewed | new attack surface | 4 |
| Worker crashes only visible in a terminal scrollback | no error tracking | 5 |

## Phases

| # | Doc | Focus | Est. |
|---|---|---|---|
| 0 | [phase-0-freeze-baseline.md](phase-0-freeze-baseline.md) | Freeze, baseline metrics, bug ledger | 0.5 d |
| 1 | [phase-1-silent-failures.md](phase-1-silent-failures.md) | Kill the silent-failure class; test the engine + verification ladder | 2–3 d |
| 2 | [phase-2-frontend-tests.md](phase-2-frontend-tests.md) | Frontend tests from zero; schema-drift guard | 3–4 d |
| 3 | [phase-3-e2e.md](phase-3-e2e.md) | Automated Playwright E2E, golden paths, CI | 3–4 d |
| 4 | [phase-4-security.md](phase-4-security.md) | Security review, tenant isolation, abuse limits | 2 d |
| 5 | [phase-5-reliability-ops.md](phase-5-reliability-ops.md) | Backups, rollback, Sentry, monitoring, load number | 2–3 d |
| 6 | [phase-6-polish-sweep.md](phase-6-polish-sweep.md) | Every screen × five states | 2–3 d |
| 7 | [phase-7-release-gate.md](phase-7-release-gate.md) | Final gate checklist + PRODUCTION.md runbook | 1 d |

**Total: ~3 weeks solo.**

## Ownership split

Claude can execute nearly all of phases 1–3 and 6, plus the audit/test halves of 4–5.

Only a human can do: Sentry project + DSNs, uptime-service signup, VPS backup cron + the restore drill, spend decisions (staging box, monitoring tier), and rotating any credentials the security pass flags.

## Standing conventions (learned the hard way)

- **Celery does not hot-reload.** Any backend change touching worker code ⇒ restart the worker locally. Prod is safe (api+worker deploy together).
- **Verify at the surface.** A fix is done when the running app shows it working (browser/API), not when the diff looks right. The `startRun`-without-`activeExecutionId` bug passed every eyeball check.
- **Ship via PR → squash auto-merge → build-publish → VPS deploy** (see `docs/deploy.md`). CI runs `tsc -b` + eslint (stricter than local `tsc --noEmit`), the node-metadata snapshot lock (`RMC_UPDATE_NODE_SNAPSHOTS=1` to refresh), and `_VALID_FIELD_TYPES` for new inspector field types.
- **No fix without a card.** Findings go on the board first.
