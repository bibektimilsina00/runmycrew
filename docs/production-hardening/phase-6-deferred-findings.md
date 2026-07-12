# Phase 6 — deferred polish findings (carded)

Fixed in the phase-6 PR: the WS-hardcode on the runs list, the dead
Settings→API-keys path, the postgres brand-icon slug. These remain — real
but architectural (crew editor reuses workflow-scoped endpoints with a crew
id), so they get their own change rather than rushing the polish PR.

## 1. Crew editor probes copilot sessions with a crew id → 404
`GET /api/v1/copilot/{crewId}/sessions` 404s on the crew editor. The
WorkflowEditor component mounts the copilot panel for crews too, but the
copilot session endpoints are workflow-scoped. Either the copilot client
must thread the entity type (`/copilot/crews/{id}/...`) or the panel should
not mount for crews. Console noise + a dead panel on every crew editor open.

## 2. Crew editor opens a collaboration WS at `/ws/workflows/{crewId}` → 404
Same root: the collaboration client always builds a `/ws/workflows/...`
URL, so for a crew it connects with a crew id against the workflows route
and the handshake 404s (two failed attempts per open). Fix: entity-aware
collab URL, or disable live-collab for crews.

Both stem from the crew editor reusing the workflow editor wholesale. The
clean fix is one entity-type parameter threaded through the copilot + collab
clients — one change, both findings.

## Non-findings (verified, no action)
- The workflow-editor "403" in the first sweep pass was the frontend Sentry
  ingest endpoint (`*.ingest.sentry.io`) returning 403, not an app request.
- Mobile 375px: **zero horizontal scroll across all 20 swept screens.**
- No other console errors on any authenticated or public screen.
