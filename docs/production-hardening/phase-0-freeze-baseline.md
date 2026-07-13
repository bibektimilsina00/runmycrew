# Phase 0 — Freeze & Baseline (0.5 day)

## Steps

- [x] **Feature freeze.** Until phase 7 closes, only `fix/`, `test/`, `chore/`, `docs/` branches merge to `main`. Branch protection stays as-is.
- [x] **Create the hardening board.** (as labeled issues #403–#410 — see note below) GitHub project "Production Hardening" with columns: `Backlog`, `In progress`, `Verify`, `Done`. Every finding from phases 1–6 becomes a card *before* it is fixed.
- [x] **Record the baseline.** Commit the numbers to this file so the after can be compared to the before:

```bash
# Backend coverage
cd apps/api && PYTHONPATH=../.. ../../.venv/bin/pytest ../../apps/api/tests -q \
  --cov=apps/api/app --cov-report=term | tail -20
```

| Metric | Baseline (2026-07-11) | After phase 7 (2026-07-12) |
|---|---|---|
| Backend tests | 820 | **924** (+104) |
| Backend coverage % | 46% (35,141 stmts, 18,944 missed) | **48%** (35,231 stmts, 18,407 missed) |
| Frontend tests | 0 | **85** |
| Automated E2E scenarios | 0 | **12** (9 spec files) + smoke gate + nightly |
| Known criticals open | 0 known (phase 1/4 audits will populate) | **0** (security fixes shipped; deferred items non-critical, carded) |

**Deployed prod SHA at freeze:** `dc39e7de` (docs: production hardening plan, #402).
**Pre-hardening dump:** `backups/pre-hardening-2026-07-11.sql.gz` (83K, 35 tables, gzip-verified) — move a copy OFF this machine.
**Board:** `hardening`-labeled issues #403–#410 (one per phase; `gh issue list -l hardening`). GitHub Project skipped — CLI token lacks `project` scope; run `gh auth refresh -s project,read:project` if you want a real board later.
**Coverage command used:** `./.venv/bin/python -m pytest apps/api/tests -q --cov=apps/api/app --cov-report=term` (pytest-cov installed via uv).

- [x] **Snapshot prod state.** Note the deployed SHA (`git log origin/main -1`) and take one manual VPS DB dump before touching anything else (phase 5 automates this):

```bash
ssh root@<vps> 'docker exec runmycrew-db-1 pg_dump -U postgres runmycrew | gzip' \
  > backups/pre-hardening-$(date +%F).sql.gz
```

## Done when

- Board exists with the phase-1 audit cards seeded.
- Baseline table above is filled in and committed.
- One verified pre-hardening DB dump exists off-VPS.
