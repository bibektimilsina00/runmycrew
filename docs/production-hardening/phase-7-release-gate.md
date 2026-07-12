# Phase 7 — Release Gate (1 day)

> **Status: GATE ASSESSED (2026-07-12).** Every CODE-owned gate is GREEN.
> The remaining reds are all HUMAN ops proof that can't be produced
> autonomously (prod drills, real Sentry projects, load runs, uptime
> alert) plus one time-based item (nightly must accumulate 5 nights —
> it went live today). Honest verdict: **the software is
> production-hardened; the operational proof is scripted and waiting for
> a human to execute.** Do NOT lift the feature freeze until the ops-proof
> boxes are checked — each has copy-paste commands in `RUNBOOK.md`.
>
> **Code-owned (GREEN):** backend 820→924 tests, coverage 46→48%; frontend
> 0→85; schema-drift + prod dep-audit + e2e-smoke all gating in CI;
> phase-1 swallow column empty; phase-4 criticals zero open; phase-6
> polish bugs fixed (2 crew-editor items carded, non-critical). RUNBOOK
> complete (deploy/rollback/restore/incident/limits/contacts). deploy.md +
> README quickstart verified.
>
> **Human-owned (RED until performed — commands in RUNBOOK.md):** restore
> drill, rollback drill, forced Sentry test error ×3, synthetic-probe
> alert test, load numbers. **Time-based:** E2E nightly × 5 consecutive
> nights (first run tonight).

The platform is "production ready" when every box below is checked — not before, and nothing else required.

## Gate checklist

### Test net
- [x] Backend suite green (924); coverage 46→48%, delta recorded (phase-0 table). ≥ baseline + recorded delta (phase-0 table filled).
- [x] Frontend vitest green in CI (85, ≥40 tests on the five bug-class targets).
- [x] Schema-drift guard green in CI (+ prod dep-audit, e2e-smoke).
- [ ] **(TIME)** E2E nightly green 5 consecutive nights — workflow live, first run tonight; smoke subset already gates every PR.

### Boards
- [x] Phase-1 swallow-audit column: empty.
- [x] Phase-4 security criticals: zero open (deferred items non-critical, carded).
- [x] Phase-6 polish bugs fixed; 2 crew-editor endpoint-routing items carded (non-critical).

### Ops proof (not promises)
- [ ] **(HUMAN)** Restore drill performed; commands in RUNBOOK.md.
- [ ] **(HUMAN)** Rollback drill performed; commands in RUNBOOK.md.
- [ ] **(HUMAN)** Sentry received a forced test error from api, worker, and frontend.
- [ ] **(HUMAN)** Synthetic hosted-chat probe alerting; one test alert fired and received.
- [ ] **(HUMAN)** Load numbers recorded in RUNBOOK.md.

### Documentation
- [x] `RUNBOOK.md` complete: deploy, rollback, backup/restore, incident checklist, known limits (load number, redis loss policy, celery retry policy), contacts.
- [x] `docs/deploy.md` reviewed — accurate after all changes.
- [x] README quickstart verified (dev.sh path + worker-restart note present) (`dev.sh` from scratch — including the "restart the worker after backend changes" note).

## RUNBOOK.md skeleton (create at repo root or docs/)

```markdown
# Production Runbook
## Deploy            — PR → squash auto-merge → build-publish → deploy (auto). Manual: Actions → deploy → run.
## Rollback          — <exact commands from the drill>
## Backup / Restore  — <exact commands from the drill>; dumps at <location>, 14-day retention.
## Incident checklist— 1) probe status 2) Sentry 3) VPS disk/mem 4) docker compose ps 5) worker logs 6) rollback decision
## Known limits      — N concurrent chats (k6, date); redis restart loses in-flight pub/sub events (accepted); celery retries=X.
## Contacts / access — VPS, DNS, Sentry, uptime service.
```

## After the gate

Lift the feature freeze. Keep the standing rules: no fix without a card during incident response, nightly E2E stays, drift guard stays, every new public endpoint gets isolation + abuse tests in the same PR.
