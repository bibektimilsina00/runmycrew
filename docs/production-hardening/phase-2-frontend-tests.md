# Phase 2 — Frontend Tests From Zero (3–4 days)

> **Status: COMPLETE (2026-07-12), branch `test/phase-2-frontend`.**
> Frontend suite 32 → 85 tests (+53 across all five targets). Tooling
> already existed (vitest wired in vite.config.ts, CI runs `pnpm test`)
> — checked off as found, not built. Fixtures captured verbatim from
> the running local API (including a crew-owned session with
> `workflow_id: null`, the canonical crash). Schema-drift guard runs in
> the Backend CI job via offline OpenAPI (`app.openapi()`, no server).
> Note discovered while capturing: for crew-owned apps the backend
> carries the crew id in `PublicAppOut.workflow_id` — opaque to the
> frontend but worth a rename someday.

There were **no meaningful** frontend tests when this was written. Target the five places real bugs shipped from, not a coverage percentage.

## 1. Tooling (half a day)

- [x] (already existed) Add `vitest` + `@testing-library/react` + `@testing-library/user-event` + `jsdom` to `apps/web`.
- [x] (already existed — `test` block in vite.config.ts) `vitest.config.ts` sharing the vite aliases; `npm run test` script.
- [x] (already existed) CI: add `vitest run` to the Frontend job in `.github/workflows/ci.yml` (red blocks merge).

## 2. Priority targets (in order — each maps to a shipped bug)

### a. `useSendMessage` (`features/public-app/hooks`) — 3 real bugs lived here
- [x] Stream event ordering: `token` accumulation, `execution_failed` sets error content, `stream_end` calls `onComplete` **exactly once** (StrictMode double-render test — the duplicate-message bug).
- [x] Ref-first ordering: `execution_failed` immediately followed by `stream_end` delivers the *error* message to `onComplete` (the "No response produced" regression).
- [x] Watchdog: no events for the timeout ⇒ error state, EventSource closed.
- [x] `session_id` rides the POST body.

### b. Zod schemas vs real payloads — the `workflow_id: null` crash class
- [x] Capture fixture JSON from the running API for: public app config (workflow + crew источник), session envelope (workflow-owned AND crew-owned), session list, message. Commit as fixtures.
- [x] Test: every fixture parses through its schema. A crew-owned session with `workflow_id: null` is the canonical regression.

### c. `useHostedListen` — today's bug (2026-07-11)
- [x] postMessage with correct origin ⇒ `startRun` **and** `setActiveExecutionId` both called (the WS-never-attached bug).
- [x] Wrong origin ignored; duplicate execution id processed once across two hook instances; listen state keyed by workflow id (no leak across editors).

### d. `useNodeExecutionStatus`
- [x] Precedence: run in flight ⇒ real per-node status wins; idle + listening ⇒ trigger pulses; terminal run + listening ⇒ pulse resumes; failed marks survive.

### e. Inspector rules (`inspector-visibility.ts`, `credential-types.ts`)
- [x] Dependent credential not hoisted above its driver; `credentialTypeByField` falls back to the driving field's default (the "does not declare a credential type" regression); action-field hoist still works for integration nodes.

## 3. Schema-drift guard (automation, not tests)

- [x] Script (`scripts/check-schema-drift.py`): dump FastAPI OpenAPI (`/openapi.json`), extract response models for the public-app + session + template endpoints, compare required/nullable fields against a committed manifest generated from the zod schemas. CI job fails on drift. Backend/frontend drift shipped twice; a human diff won't catch the third.

## Done when

- 40–60 tests across targets a–e, all green in CI.
- Drift-guard job in CI, currently green.
- One StrictMode-specific test exists and fails if `onComplete` moves back inside a `setState` updater.
