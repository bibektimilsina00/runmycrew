# Phase 3 — Automated E2E (3–4 days)

Every major bug this July was found by *manual* Playwright driving. Codify those sessions so they run without a human.

## 1. Harness (1 day)

- [ ] `apps/web/e2e/` Playwright suite (`@playwright/test`), separate from vitest.
- [ ] `docker-compose.e2e.yml`: api + worker + db + redis + built web. **Worker always rebuilds from the current tree** — the stale-worker/celery-no-reload trap produced four false bug reports locally; CI must never have that ambiguity.
- [ ] Seed script (`e2e/seed.ts` or API calls in global-setup): test user, workspace, one fake LLM credential.
- [ ] **Fake LLM provider:** a mock HTTP server standing in for the provider base URL (or an echo node), so agent/evaluator paths run deterministically with **no real API keys in CI**. The evaluator mock returns parseable metric JSON.

## 2. Golden-path scenarios (business-value order)

- [ ] **Auth:** register → login → land on dashboard.
- [ ] **Workflow basics:** create → drop Manual trigger + node → Run → log panel shows per-node statuses → node marks on canvas.
- [ ] **Form trigger:** create with Form trigger (fields) → Run → hosted form tab opens → only the form until submit → submit → values in execution output → run streams into the editor.
- [ ] **Chat app:** crew with Chat App trigger → Run → auto-activate → chat tab → "Listening…" → send message → run streams live (trigger completes, downstream lights) → reply renders as markdown → conversation sidebar: New chat, switch, history isolation.
- [ ] **Crew loop (deterministic):** install `crew-expense-precheck-gate` template → within-policy ⇒ `success` round 1; over-policy ⇒ `stalled` round 2 with real assertion feedback. This template IS the crew-mechanics test.
- [ ] **Crew loop (mock LLM):** support-answerer template against the fake provider → rounds run → judge verdict path → reply.
- [ ] **Templates:** gallery renders graph previews; detail page; install → editor opens with graph.
- [ ] **Error paths:** agent without credential → red error card in chat with the real reason; log panel structured error card; crew round failure surfaces `Crew round N failed: …`.
- [ ] **Multi-tenant smoke:** second user cannot open first user's workflow URL (403/404).

## 3. CI wiring

- [ ] Nightly workflow: full suite against compose. Failures open an issue automatically.
- [ ] PR smoke subset: auth + workflow-run + form-submit (fastest three) — full suite per-PR is too slow.
- [ ] Artifacts on failure: Playwright traces + screenshots uploaded.

## Done when

- `npm run e2e` green locally from a clean checkout in one command.
- Nightly CI job exists and has passed 3 consecutive nights.
- Each scenario above maps to a spec file; none skipped.
