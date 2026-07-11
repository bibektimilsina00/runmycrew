# Phase 1 — Kill the Silent-Failure Class (2–3 days)

The July findings were four symptoms of one disease: code that fails without telling anyone. This phase hunts the remaining instances and puts tests where the known ones lived.

## 1. Exception-swallow audit

- [ ] Enumerate every silent catch:

```bash
grep -rn "except Exception" apps/api/app apps/worker/app --include="*.py" \
  | grep -v pycache > /tmp/swallows.txt
# For each hit, inspect the handler body:
grep -rn -A3 "except Exception" apps/api/app apps/worker/app --include="*.py" | grep -v pycache
```

- [ ] For **every** hit, one of three outcomes (card per file):
  1. Logs at `error`/`warning` **and** persists a user-visible failure state (like `_fail_app_message` does), or
  2. Re-raises / converts to an HTTP error, or
  3. Gets a comment proving silence is correct (e.g. best-effort cache write) — reviewer must agree.
- [ ] Known repeat offender to re-check: `polling_node_factory.py` register swallow (circular-import class). Add a startup assertion: after `eager_register_polling_providers()`, poller count must be ≥ a committed constant, else log.error loudly.

## 2. Fallback-branch audit (the L1 bug class)

Every "when in doubt return something truthy/empty" branch gets a garbage-input test:

- [ ] `template_resolver.evaluate_condition` — malformed expr, unresolvable path, empty lhs, non-numeric comparison. (Literal-comparison fix landed 2026-07-11; lock it with tests.)
- [ ] `expression_engine._step_data` / `$node()` / `$trigger` — missing provenance, unknown labels, non-dict context.
- [ ] `tasks._extract_reply` — outputs with no `content`, nested crews, artifacts-only outputs.
- [ ] `trigger/form.py _coerce` — junk strings for every declared type.
- [ ] `nodeUtils.matchesCondition` (frontend, phase 2 file) — unknown operator, missing field.

## 3. Verification-ladder contract tests (`apps/api/tests/test_verification_ladder.py`)

The product's core promise had zero tests. Cover:

- [ ] **L1 expression:** true case, false case, malformed expression, template that resolves empty ⇒ must be `passed=False`, never truthy-default.
- [ ] **L2 rule:** every `ruleType` (`contains`, `not_contains`, `regex`, `required_keys`) × pass/fail/garbage-subject.
- [ ] **L3 http/code:** unreachable URL, non-200, sandbox error ⇒ `passed=False` with feedback, node still `success=True` (verdict, not crash).
- [ ] **L4 evaluator:** model returns unparseable JSON, missing metrics, `passed` absent ⇒ falls back to the ≥60% rule, never crashes.

## 4. Crew-loop contract tests (`apps/api/tests/test_crew_loop.py`)

Deterministic fixture graphs (form → crew → verify), no LLM:

- [ ] Every terminal state reachable: `success` (round 1 pass), `stalled` (stagnation), `exhausted` (maxRounds), `blocked` (round hard-fails ⇒ `success=False` with `Crew round N failed: …`), `no_op`.
- [ ] Round payload contract: `goal`, `round`, `feedback` present; `$step.*`, `$trigger.*` resolve inside rounds (regression: 2026-07-11 `$step` fix, `_trigger_data` fix).
- [ ] `run_downstream` failure propagation: failed sub-run returns `{status: failed, error}` — never `{}`.
- [ ] Budget: `maxCostUsd` exceeded ⇒ `exhausted`.

## 5. Template-syntax lint test

- [ ] Test that walks `apps/api/app/features/templates/seeds/**/*.json` **and** `apps/web/src/features/loops/utils/crewPresets.ts`, extracts every `{{...}}`, and asserts the prefix is one of the resolvable forms (`$step`, `$trigger`, `$node(`, `$json` bare, `$vars`, `$env`, `loop.`). `$json.path` shipped broken in our own presets — make that impossible to repeat.

## Done when

- `/tmp/swallows.txt` derived board column is empty (every hit resolved 1/2/3).
- The four test files above exist and pass; backend suite grows by ≥50 meaningful tests.
- Baseline coverage number moves up and is recorded in phase-0 table.
