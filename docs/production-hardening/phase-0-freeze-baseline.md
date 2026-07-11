# Phase 0 — Freeze & Baseline (0.5 day)

## Steps

- [ ] **Feature freeze.** Until phase 7 closes, only `fix/`, `test/`, `chore/`, `docs/` branches merge to `main`. Branch protection stays as-is.
- [ ] **Create the hardening board.** GitHub project "Production Hardening" with columns: `Backlog`, `In progress`, `Verify`, `Done`. Every finding from phases 1–6 becomes a card *before* it is fixed.
- [ ] **Record the baseline.** Commit the numbers to this file so the after can be compared to the before:

```bash
# Backend coverage
cd apps/api && PYTHONPATH=../.. ../../.venv/bin/pytest ../../apps/api/tests -q \
  --cov=apps/api/app --cov-report=term | tail -20
```

| Metric | Baseline (fill in) | After phase 7 |
|---|---|---|
| Backend tests | 820 | |
| Backend coverage % | | |
| Frontend tests | 0 | |
| Automated E2E scenarios | 0 | |
| Known criticals open | | |

- [ ] **Snapshot prod state.** Note the deployed SHA (`git log origin/main -1`) and take one manual VPS DB dump before touching anything else (phase 5 automates this):

```bash
ssh root@<vps> 'docker exec runmycrew-db-1 pg_dump -U postgres runmycrew | gzip' \
  > backups/pre-hardening-$(date +%F).sql.gz
```

## Done when

- Board exists with the phase-1 audit cards seeded.
- Baseline table above is filled in and committed.
- One verified pre-hardening DB dump exists off-VPS.
