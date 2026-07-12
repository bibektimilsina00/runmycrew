# Phase 3 — Automated E2E (3–4 days)

> **Status: COMPLETE (2026-07-12), branch `test/phase-3-e2e`.**
> 9 spec files / 12 tests, twice-consecutive green against the compose
> stack (`pnpm e2e` from apps/web). The suite immediately earned its
> keep — real bugs found while writing it (specs carry workaround
> comments; fixes are the next branch):
> 1. **Linear crew chains never see the verdict** — `_execute_subgraph`
>    returns the START node's output while `agent_crew` reads `sub[-1]`;
>    a `crew → agent → evaluator` chain exhausts every round.
> 2. **Crew-hosted chat replies "No response produced"** — worker
>    `_extract_reply` only reads `output.content`; crew answers nest
>    under `output.result`.
> 3. **Token streaming is dead wiring** — frontend listens for `token`
>    SSE, backend emits `agent_chunk`; replies render only at completion.
> 4. **Fast form submits lose the visitor's transcript entry
>    permanently** — `useAppendMessage` drops the optimistic append
>    pre-hydration and nothing refetches.
> 5. `GET /executions/?workflow_id=…` 500s (`ExecutionOut.logs` lazy-load
>    outside the async session).
> 6. `buildWsUrl()` hardcodes `localhost:8000` for the `localhost`
>    hostname — editor Logs panel dead on any non-dev host.
> 7. Agent node silently falls back to ANY same-type credential of the
>    owner when the configured one is missing.
> 8. FormField labels never wire `htmlFor` to inputs (a11y; forces
>    placeholder selectors).
> Nightly has to pass 3 consecutive nights before this phase's gate
> fully closes — workflow is live, watch it.

Every major bug this July was found by *manual* Playwright driving. Codify those sessions so they run without a human.

## 1. Harness (1 day)

- [x] `apps/web/e2e/` Playwright suite (`@playwright/test`), separate from vitest.
- [x] `docker-compose.e2e.yml`: api + worker + db + redis + built web. **Worker always rebuilds from the current tree** — the stale-worker/celery-no-reload trap produced four false bug reports locally; CI must never have that ambiguity.
- [x] Seed script (`e2e/seed.ts` or API calls in global-setup): test user, workspace, one fake LLM credential.
- [x] **Fake LLM provider:** a mock HTTP server standing in for the provider base URL (or an echo node), so agent/evaluator paths run deterministically with **no real API keys in CI**. The evaluator mock returns parseable metric JSON.

## 2. Golden-path scenarios (business-value order)

- [x] **Auth:** register → login → land on dashboard.
- [x] **Workflow basics:** create → drop Manual trigger + node → Run → log panel shows per-node statuses → node marks on canvas.
- [x] **Form trigger:** create with Form trigger (fields) → Run → hosted form tab opens → only the form until submit → submit → values in execution output → run streams into the editor.
- [x] **Chat app:** crew with Chat App trigger → Run → auto-activate → chat tab → "Listening…" → send message → run streams live (trigger completes, downstream lights) → reply renders as markdown → conversation sidebar: New chat, switch, history isolation.
- [x] **Crew loop (deterministic):** install `crew-expense-precheck-gate` template → within-policy ⇒ `success` round 1; over-policy ⇒ `stalled` round 2 with real assertion feedback. This template IS the crew-mechanics test.
- [x] **Crew loop (mock LLM):** support-answerer template against the fake provider → rounds run → judge verdict path → reply.
- [x] **Templates:** gallery renders graph previews; detail page; install → editor opens with graph.
- [x] **Error paths:** agent without credential → red error card in chat with the real reason; log panel structured error card; crew round failure surfaces `Crew round N failed: …`.
- [x] **Multi-tenant smoke:** second user cannot open first user's workflow URL (403/404).

## 3. CI wiring

- [x] Nightly workflow: full suite against compose. Failures open an issue automatically.
- [x] PR smoke subset: auth + workflow-run + form-submit (fastest three) — full suite per-PR is too slow.
- [x] Artifacts on failure: Playwright traces + screenshots uploaded.

## Done when

- `npm run e2e` green locally from a clean checkout in one command.
- Nightly CI job exists and has passed 3 consecutive nights.
- Each scenario above maps to a spec file; none skipped.
