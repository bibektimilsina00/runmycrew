# Phase 6 — Product Polish Sweep (2–3 days)

> **Status: SWEEP DONE (2026-07-12), branch `test/phase-6-polish`.**
> Automated Playwright sweep (`e2e/specs/polish-sweep.spec.ts`, opt-in via
> `POLISH=1`) walked all 20 authenticated + editor + not-found screens at
> 1440px and 375px, capturing console errors, failed requests, and
> horizontal-scroll. Machine-checkable results:
> **mobile 375px is clean — zero horizontal scroll on every screen.**
> Three real bugs found and fixed here:
> 1. `/runs` live-updates were dead off-localhost — `useRuns.ts` kept the
>    same `localhost:8000` WS hardcode phase-3 fixed in `useRunStream`
>    (both now share `apiWsBaseUrl()`).
> 2. **Settings → API keys was 404** — the frontend called
>    `/users/api-keys` but the backend mounts `/api-keys`.
> 3. The PostgreSQL credential's `icon_slug` didn't match its shipped
>    `postgresql.svg`, so `/icons/postgres` 404'd to a blank tile.
> Two crew-editor endpoint-routing findings (copilot + collab WS use the
> workflow path with a crew id) are carded in
> `phase-6-deferred-findings.md`. The five-states-per-screen visual pass
> (empty/loading/error nuance) is a human review of the captured
> screenshots — the automated sweep covers the mechanical states.

Systematic, not aesthetic. Every screen gets checked against the same five states; every gap becomes a card; fixes land in batches. Claude runs the sweep with Playwright screenshots and hands over the annotated gap list.

## The five states (per screen)

1. **Empty** — brand-new workspace, zero data. No blank voids; every empty state says what to do next.
2. **Loading** — skeletons or spinners; no layout jump when content lands.
3. **Error** — API down / 500: a readable message with a retry, never a white screen or infinite spinner.
4. **Mobile 375px** — no horizontal scroll, controls reachable, text readable.
5. **Keyboard** — tab order sane, focus visible, Esc closes modals/popovers, Enter submits.

## Screen inventory

| Screen | Empty | Loading | Error | 375px | Keyboard |
|---|---|---|---|---|---|
| Dashboard / Home | ☐ | ☐ | ☐ | ☐ | ☐ |
| Automations list | ☐ | ☐ | ☐ | ☐ | ☐ |
| Workflow editor — canvas | ☐ | ☐ | ☐ | ☐ | ☐ |
| Editor — Library panel | ☐ | ☐ | ☐ | ☐ | ☐ |
| Editor — Inspector (agent node) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Editor — Logs panel + ErrorView | ☐ | ☐ | ☐ | ☐ | ☐ |
| Editor — Copilot panel | ☐ | ☐ | ☐ | ☐ | ☐ |
| Crew editor (mode differences) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Templates gallery | ☐ | ☐ | ☐ | ☐ | ☐ |
| Template detail | ☐ | ☐ | ☐ | ☐ | ☐ |
| My templates + publish modal | ☐ | ☐ | ☐ | ☐ | ☐ |
| Integrations (Connections) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Connect-credential modal (OAuth + key) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Skills list + editor | ☐ | ☐ | ☐ | ☐ | ☐ |
| Personas | ☐ | ☐ | ☐ | ☐ | ☐ |
| Executions / runs history | ☐ | ☐ | ☐ | ☐ | ☐ |
| Settings (workspace, members) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Auth: login / register / reset | ☐ | ☐ | ☐ | ☐ | ☐ |
| **Hosted chat page** (public) | ☐ | ☐ | ☐ | ☐ | ☐ |
| **Hosted form page** (public) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Public app: password gate | ☐ | ☐ | ☐ | ☐ | ☐ |
| 404 / not-found routes | ☐ | ☐ | ☐ | ☐ | ☐ |

## Method

1. Fresh test workspace (true empty states) + a populated one.
2. Playwright sweep script screenshots each screen in each state (throttle network for loading; kill the API container for error states).
3. File cards per gap with the screenshot attached; batch-fix per feature area; re-run the sweep to close.

## Also in this pass

- [ ] Console-noise zero: no React warnings (the ErrorView button-nesting hydration warning seen 2026-07-11 is a known card), no failed-resource 404s on any screen.
- [ ] Copy pass: every toast/error message says what happened *and* what to do.
- [ ] Favicon/title/meta on hosted public pages (they represent the customer's brand).

## Done when

- Every cell in the inventory table is checked.
- Gap cards: zero open.
- Console clean on every screen.
