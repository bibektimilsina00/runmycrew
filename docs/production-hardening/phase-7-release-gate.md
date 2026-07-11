# Phase 7 — Release Gate (1 day)

The platform is "production ready" when every box below is checked — not before, and nothing else required.

## Gate checklist

### Test net
- [ ] Backend suite green; coverage ≥ baseline + recorded delta (phase-0 table filled).
- [ ] Frontend vitest suite green in CI (≥40 tests on the five bug-class targets).
- [ ] Schema-drift guard green in CI.
- [ ] E2E nightly green **5 consecutive nights**.

### Boards
- [ ] Phase-1 swallow-audit column: empty.
- [ ] Phase-4 security criticals: zero open.
- [ ] Phase-6 polish cards: zero open.

### Ops proof (not promises)
- [ ] Restore drill performed; commands in RUNBOOK.md.
- [ ] Rollback drill performed; commands in RUNBOOK.md.
- [ ] Sentry received a forced test error from api, worker, and frontend.
- [ ] Synthetic hosted-chat probe alerting; one test alert fired and received.
- [ ] Load numbers recorded in RUNBOOK.md.

### Documentation
- [ ] `RUNBOOK.md` complete: deploy, rollback, backup/restore, incident checklist, known limits (load number, redis loss policy, celery retry policy), contacts.
- [ ] `docs/deploy.md` still accurate after all changes.
- [ ] README quickstart works on a clean machine (`dev.sh` from scratch — including the "restart the worker after backend changes" note).

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
