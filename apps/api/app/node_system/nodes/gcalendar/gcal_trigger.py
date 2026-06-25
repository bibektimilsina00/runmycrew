"""Google Calendar trigger node — syncToken-driven polling.

Fires once per added / updated / cancelled event in the watched
calendar that matches the user's filter.

The cursor lives in `integration_trigger_state.cursor` (per workflow /
node) and is Calendar's `nextSyncToken`. Mechanics:

  1. On the first invocation, we list events starting from `now` with
     `singleEvents=true&showDeleted=true` so cancellations come through
     too. We persist the response's `nextSyncToken` but emit *nothing* —
     fresh triggers should fire on what changes next, not what already
     exists in the calendar.
  2. Subsequent invocations call `events.list?syncToken=<token>`. The
     response enumerates every event that has been added / updated /
     cancelled since then. We filter by the user's `event_filter`
     (any / created / updated / cancelled) + optional free-text `q`,
     normalise each surviving event, and advance the cursor in the
     same transaction the matches get dispatched in.
  3. On `410 GONE` (Google retires sync tokens after ~30 days), we
     re-bootstrap: re-snapshot from `now`, drop any pending matches,
     keep the trigger healthy without operator intervention.

Mirrors what n8n / Zapier / Pipedream do under the hood for Calendar
(`events.list` with `syncToken`). Polling cadence comes from the
scheduler's per-row `next_poll_at` field.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.models import IntegrationTriggerState
from apps.api.app.features.triggers.repository import IntegrationTriggerStateRepository
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

GCAL_API = "https://www.googleapis.com/calendar/v3"
PROVIDER = "gcalendar"
DEFAULT_POLL_INTERVAL_SECONDS = 60

EVENT_FILTERS = ("any", "created", "updated", "cancelled")


class GCalTriggerProperties(BaseModel):
    credential: str | None = None
    calendar_id: str = "primary"
    event_filter: str = "any"
    # Calendar's free-text `q` parameter — matches against summary,
    # description, location, attendee email, organizer.
    query: str = ""
    max_events_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS


class GCalTriggerNode(BaseNode[GCalTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GCalTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gcal_event",
            name="Google Calendar",
            category="trigger",
            description=(
                "Fires once per added / updated / cancelled event matching your "
                "filter. Uses Calendar's `syncToken` cursor so each poll only "
                "surfaces what changed since the last run — no duplicates."
            ),
            icon="google-calendar",
            color="#1c1c1c",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "calendar_id",
                    "label": "Calendar",
                    "type": "string",
                    "default": "primary",
                    "placeholder": "primary",
                    "description": (
                        "Calendar ID to watch. `primary` is the account's main "
                        "calendar. Find IDs for shared calendars in Calendar "
                        "settings → Integrate calendar."
                    ),
                },
                {
                    "name": "event_filter",
                    "label": "Event type",
                    "type": "options",
                    "default": "any",
                    "options": [
                        {"label": "Any change", "value": "any"},
                        {"label": "Created", "value": "created"},
                        {"label": "Updated", "value": "updated"},
                        {"label": "Cancelled", "value": "cancelled"},
                    ],
                },
                {
                    "name": "query",
                    "label": "Search query",
                    "type": "string",
                    "default": "",
                    "placeholder": "team standup",
                    "description": (
                        "Optional free-text filter — Calendar matches against "
                        "summary, description, location, attendees, organizer."
                    ),
                },
                {
                    "name": "max_events_per_poll",
                    "label": "Max events per poll",
                    "type": "number",
                    "default": 25,
                    "mode": "advanced",
                    "description": (
                        "Hard cap on how many events a single poll emits. "
                        "Protects against backlog spikes after downtime."
                    ),
                },
                {
                    "name": "poll_interval_seconds",
                    "label": "Poll interval (seconds)",
                    "type": "number",
                    "default": DEFAULT_POLL_INTERVAL_SECONDS,
                    "mode": "advanced",
                    "description": (
                        "How often the background scheduler asks Calendar for "
                        "changes. Minimum 30s to stay inside Google's quota."
                    ),
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "status", "type": "string"},
                {"label": "summary", "type": "string"},
                {"label": "description", "type": "string"},
                {"label": "location", "type": "string"},
                {"label": "start", "type": "string"},
                {"label": "end", "type": "string"},
                {"label": "htmlLink", "type": "string"},
                {"label": "organizer_email", "type": "string"},
                {"label": "attendee_emails", "type": "array"},
                {"label": "change_type", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # The poller dispatches a pre-normalised event envelope per
        # match; pass it through verbatim so downstream nodes see the
        # same shape whether the trigger fired live or via fixture replay.
        if isinstance(input_data, dict) and input_data.get("id") and input_data.get("payload"):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        workflow_id = getattr(context, "workflow_id", None)
        node_id = getattr(context, "node_id", None)
        workspace_id = getattr(context, "workspace_id", None)
        db = getattr(context, "db", None)
        wf_uuid = _safe_uuid(workflow_id)
        ws_uuid = _safe_uuid(workspace_id)
        if wf_uuid is None or ws_uuid is None or db is None or not node_id:
            return await self._stateless_first_match(token)

        repo = IntegrationTriggerStateRepository(db)
        state = await repo.get(wf_uuid, node_id)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Authorization": f"Bearer {token}"}
                if state is None:
                    sync_token = await self._snapshot_sync_token(client, headers)
                    await repo.upsert(
                        workflow_id=wf_uuid,
                        workspace_id=ws_uuid,
                        node_id=node_id,
                        provider=PROVIDER,
                        cursor={"sync_token": sync_token},
                        next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
                        last_error=None,
                    )
                    await db.commit()
                    return NodeResult(
                        success=True,
                        output_data={
                            "matched": 0,
                            "events": [],
                            "cursor_initialised": True,
                            "sync_token": sync_token,
                        },
                        # Cursor initialised, nothing to emit yet — halt the
                        # downstream chain so action nodes don't fire with
                        # null fields. Real events arrive via the scheduler.
                        handled_successors=True,
                    )
                events, new_sync_token = await self._poll_sync(client, headers, state)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Calendar API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GCalTriggerNode poll failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))

        await repo.upsert(
            workflow_id=wf_uuid,
            workspace_id=ws_uuid,
            node_id=node_id,
            provider=PROVIDER,
            cursor={"sync_token": new_sync_token},
            next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
            last_error=None,
        )
        await db.commit()

        if not events:
            return NodeResult(
                success=True,
                output_data={
                    "matched": 0,
                    "events": [],
                    "sync_token": new_sync_token,
                },
                # Nothing matched this poll — halt downstream so the
                # action chain only fires when there is real event data.
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=events[0])

    # ── public poll API (scheduler + inline preview share this) ──────

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], str]:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            if not cursor or not cursor.get("sync_token"):
                sync_token = await self._snapshot_sync_token(client, headers)
                return [], sync_token
            return await self._poll_sync(client, headers, cursor)

    async def _snapshot_sync_token(self, client: httpx.AsyncClient, headers: dict[str, str]) -> str:
        """Bootstrap path — page through `events.list` from `now` until
        Google hands us a `nextSyncToken`. Each page only includes
        events ahead of `timeMin`, so this is cheap even on busy
        calendars. We emit nothing — only the token is kept."""
        cal_id = self.props.calendar_id or "primary"
        params: dict[str, Any] = {
            "singleEvents": "true",
            "showDeleted": "true",
            "timeMin": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "maxResults": 250,
        }
        sync_token = ""
        page_token: str | None = None
        while True:
            if page_token:
                params["pageToken"] = page_token
            resp = await client.get(
                f"{GCAL_API}/calendars/{cal_id}/events", headers=headers, params=params
            )
            resp.raise_for_status()
            body = resp.json()
            sync_token = str(body.get("nextSyncToken") or sync_token)
            page_token = body.get("nextPageToken")
            if sync_token or not page_token:
                break
        return sync_token

    async def _poll_sync(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        cursor_or_state: IntegrationTriggerState | dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str]:
        """Pull every event changed since the cursor, filter, normalise,
        return `(matches, new_sync_token)`. Pagination drains the
        delta window before we commit the new token."""
        cursor = (
            cursor_or_state.cursor
            if isinstance(cursor_or_state, IntegrationTriggerState)
            else cursor_or_state
        )
        sync_token = str((cursor or {}).get("sync_token") or "")
        if not sync_token:
            return [], await self._snapshot_sync_token(client, headers)

        cal_id = self.props.calendar_id or "primary"
        event_filter = (self.props.event_filter or "any").lower()
        if event_filter not in EVENT_FILTERS:
            event_filter = "any"
        query = (self.props.query or "").strip()
        max_take = max(1, min(self.props.max_events_per_poll, 100))

        matches: list[dict[str, Any]] = []
        new_sync_token = sync_token
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {"syncToken": sync_token, "maxResults": 250}
            if page_token:
                params["pageToken"] = page_token
            if query:
                # Note: Google docs say `q` is only valid on full sync,
                # not incremental. We pass it for filtering-by-text on
                # the bootstrap path; for sync delta we filter
                # client-side below to avoid the 400 error.
                pass
            resp = await client.get(
                f"{GCAL_API}/calendars/{cal_id}/events", headers=headers, params=params
            )
            if resp.status_code == 410:
                # Sync token expired (>30d). Re-bootstrap; drop pending
                # matches so we don't double-emit anything that may
                # also surface in the snapshot.
                return [], await self._snapshot_sync_token(client, headers)
            resp.raise_for_status()
            body = resp.json()
            page_events = body.get("items") or []
            for ev in page_events:
                change_type = _classify_change(ev)
                if event_filter != "any" and change_type != event_filter:
                    continue
                if query and not _matches_query(ev, query):
                    continue
                matches.append(_normalize(ev, change_type))
                if len(matches) >= max_take:
                    break
            page_token = body.get("nextPageToken")
            new_sync_token = str(body.get("nextSyncToken") or new_sync_token)
            if len(matches) >= max_take or not page_token:
                break
        return matches, new_sync_token

    async def _stateless_first_match(self, token: str) -> NodeResult:
        """Preview path — return the next upcoming event without writing
        a cursor. Only used in synthetic test runs without a workflow."""
        headers = {"Authorization": f"Bearer {token}"}
        cal_id = self.props.calendar_id or "primary"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                params: dict[str, Any] = {
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "timeMin": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "maxResults": 1,
                }
                query = (self.props.query or "").strip()
                if query:
                    params["q"] = query
                resp = await client.get(
                    f"{GCAL_API}/calendars/{cal_id}/events",
                    headers=headers,
                    params=params,
                )
                resp.raise_for_status()
                items = resp.json().get("items") or []
                if not items:
                    return NodeResult(
                        success=True,
                        output_data={"matched": 0, "events": []},
                        handled_successors=True,
                    )
                return NodeResult(
                    success=True,
                    output_data=_normalize(items[0], _classify_change(items[0])),
                )
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Calendar API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GCalTriggerNode stateless poll failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── helpers ──────────────────────────────────────────────────────────────


def _safe_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _next_poll_at(interval_seconds: int) -> datetime:
    seconds = max(30, min(int(interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS), 60 * 60))
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _classify_change(event: dict[str, Any]) -> str:
    """Sort each event into created / updated / cancelled.

    Calendar doesn't expose a `change_type` field. We use:
      - `status == cancelled` → cancelled
      - `created == updated` (within 1s) → created
      - else → updated
    """
    if (event.get("status") or "").lower() == "cancelled":
        return "cancelled"
    created = event.get("created")
    updated = event.get("updated")
    if created and updated:
        try:
            c = datetime.fromisoformat(created.replace("Z", "+00:00"))
            u = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            if abs((u - c).total_seconds()) <= 1:
                return "created"
        except ValueError:
            pass
    return "updated"


def _matches_query(event: dict[str, Any], query: str) -> bool:
    """Mimic Calendar's `q` matching for the incremental-sync path
    where the API rejects `q`. Case-insensitive substring against the
    same fields the server-side search indexes."""
    q = query.lower()
    haystacks = [
        event.get("summary") or "",
        event.get("description") or "",
        event.get("location") or "",
        (event.get("organizer") or {}).get("email") or "",
    ]
    for att in event.get("attendees") or []:
        if isinstance(att, dict):
            haystacks.append(att.get("email") or "")
            haystacks.append(att.get("displayName") or "")
    return any(q in str(h).lower() for h in haystacks)


def _normalize(event: dict[str, Any], change_type: str) -> dict[str, Any]:
    """Flatten the Calendar event into the shape our outputs_schema
    advertises. Downstream nodes template `{{ $step.summary }}` /
    `{{ $step.start }}` without parsing the event tree."""
    start = event.get("start") or {}
    end = event.get("end") or {}
    organizer = event.get("organizer") or {}
    attendee_emails = [
        a.get("email")
        for a in (event.get("attendees") or [])
        if isinstance(a, dict) and a.get("email")
    ]
    return {
        "id": event.get("id"),
        "status": event.get("status") or "",
        "summary": event.get("summary") or "",
        "description": event.get("description") or "",
        "location": event.get("location") or "",
        "start": start.get("dateTime") or start.get("date") or "",
        "end": end.get("dateTime") or end.get("date") or "",
        "htmlLink": event.get("htmlLink") or "",
        "organizer_email": organizer.get("email") or "",
        "attendee_emails": attendee_emails,
        "change_type": change_type,
        "payload": event,
    }


# ── scheduler integration ────────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Adapter — lets the polling scheduler drive a Calendar poll
    without instantiating a full `GCalTriggerNode`. Builds a minimal
    property bundle off the saved node props, runs one poll, returns
    `(matches, new_cursor_dict)`."""
    node = GCalTriggerNode.__new__(GCalTriggerNode)
    node.props = GCalTriggerProperties(
        credential=None,
        calendar_id=str(props.get("calendar_id") or "primary"),
        event_filter=str(props.get("event_filter") or "any"),
        query=str(props.get("query") or ""),
        max_events_per_poll=int(props.get("max_events_per_poll") or 25),
        poll_interval_seconds=int(
            props.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS
        ),
    )
    events, new_sync_token = await node.poll(token, cursor)
    return events, {"sync_token": new_sync_token}


def _register() -> None:
    try:
        from apps.api.app.execution_engine.scheduler.integration_polling import (
            register_poller,
        )
    except Exception:  # noqa: BLE001
        return
    register_poller(
        node_type="trigger.gcal_event",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()
