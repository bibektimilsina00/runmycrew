"""Google Calendar action node — consolidated CRUD over a single
calendar via the user's OAuth credential.

One node, six operations:
  - `create_event`  / `update_event`  / `delete_event`
  - `get_event`     / `list_events`   / `quick_add`

The shape mirrors `GmailNode` and the consolidated Meta nodes — every
operation lives on the same node with a top-level `operation` dropdown
and per-op fields gated by `condition`. Keeps the inspector tidy and
keeps the registry from sprawling into a node-per-verb explosion.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

GCAL_API = "https://www.googleapis.com/calendar/v3"


# Common IANA time-zones surfaced in the inspector as a searchable
# dropdown with allowCustom so power users can paste any IANA name the
# calendar accepts (`Antarctica/Troll`, etc).
_TIMEZONE_OPTIONS: list[dict[str, str]] = [
    {"label": "Calendar default (blank)", "value": ""},
    {"label": "UTC", "value": "UTC"},
    {"label": "US — Eastern (New York)", "value": "America/New_York"},
    {"label": "US — Central (Chicago)", "value": "America/Chicago"},
    {"label": "US — Mountain (Denver)", "value": "America/Denver"},
    {"label": "US — Mountain (Phoenix, no DST)", "value": "America/Phoenix"},
    {"label": "US — Pacific (Los Angeles)", "value": "America/Los_Angeles"},
    {"label": "US — Alaska", "value": "America/Anchorage"},
    {"label": "US — Hawaii", "value": "Pacific/Honolulu"},
    {"label": "Canada — Toronto", "value": "America/Toronto"},
    {"label": "Canada — Vancouver", "value": "America/Vancouver"},
    {"label": "Brazil — São Paulo", "value": "America/Sao_Paulo"},
    {"label": "Mexico City", "value": "America/Mexico_City"},
    {"label": "UK — London", "value": "Europe/London"},
    {"label": "Ireland — Dublin", "value": "Europe/Dublin"},
    {"label": "France — Paris", "value": "Europe/Paris"},
    {"label": "Germany — Berlin", "value": "Europe/Berlin"},
    {"label": "Spain — Madrid", "value": "Europe/Madrid"},
    {"label": "Italy — Rome", "value": "Europe/Rome"},
    {"label": "Netherlands — Amsterdam", "value": "Europe/Amsterdam"},
    {"label": "Russia — Moscow", "value": "Europe/Moscow"},
    {"label": "UAE — Dubai", "value": "Asia/Dubai"},
    {"label": "India — Kolkata", "value": "Asia/Kolkata"},
    {"label": "Nepal — Kathmandu", "value": "Asia/Kathmandu"},
    {"label": "Bangladesh — Dhaka", "value": "Asia/Dhaka"},
    {"label": "Thailand — Bangkok", "value": "Asia/Bangkok"},
    {"label": "Singapore", "value": "Asia/Singapore"},
    {"label": "Hong Kong", "value": "Asia/Hong_Kong"},
    {"label": "China — Shanghai", "value": "Asia/Shanghai"},
    {"label": "Japan — Tokyo", "value": "Asia/Tokyo"},
    {"label": "South Korea — Seoul", "value": "Asia/Seoul"},
    {"label": "Australia — Sydney", "value": "Australia/Sydney"},
    {"label": "Australia — Melbourne", "value": "Australia/Melbourne"},
    {"label": "Australia — Perth", "value": "Australia/Perth"},
    {"label": "New Zealand — Auckland", "value": "Pacific/Auckland"},
]


class GCalProperties(BaseModel):
    credential: str | None = None
    operation: str = "create_event"
    calendar_id: str = "primary"

    # create / update
    event_id: str | None = None
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    start: str | None = None  # ISO 8601 datetime OR YYYY-MM-DD for all-day
    end: str | None = None
    time_zone: str | None = None
    all_day: bool = False
    attendees: str | None = None  # CSV emails
    send_notifications: bool = False

    # list
    query: str | None = None
    time_min: str | None = None
    time_max: str | None = None
    max_results: int = 25
    order_by: str = "startTime"

    # quick_add
    text: str | None = None


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GCalNode(BaseNode[GCalProperties]):
    @classmethod
    def get_properties_model(cls):
        return GCalProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gcal",
            name="Google Calendar",
            category="integration",
            description=(
                "Create, update, delete, search Google Calendar events via OAuth. "
                "One node, six operations — pick from the dropdown."
            ),
            icon="si:SiGooglecalendar",
            color="#4285f4",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "create_event",
                    "options": [
                        {"label": "Create Event", "value": "create_event"},
                        {"label": "Update Event", "value": "update_event"},
                        {"label": "Delete Event", "value": "delete_event"},
                        {"label": "Get Event", "value": "get_event"},
                        {"label": "List Events", "value": "list_events"},
                        {"label": "Quick Add (natural language)", "value": "quick_add"},
                    ],
                },
                {
                    "name": "calendar_id",
                    "label": "Calendar",
                    "type": "string",
                    "default": "primary",
                    "placeholder": "primary",
                    "description": (
                        "Calendar ID. `primary` is the account's main calendar. "
                        "Find IDs for shared calendars in Calendar settings → "
                        "Integrate calendar."
                    ),
                },
                # ── event_id — required for update / delete / get ───
                {
                    "name": "event_id",
                    "label": "Event ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $trigger.id }}",
                    "condition": _cond_any("update_event", "delete_event", "get_event"),
                },
                # ── content fields — create / update ────────────────
                {
                    "name": "summary",
                    "label": "Title",
                    "type": "string",
                    "placeholder": "Team standup",
                    "required": True,
                    "condition": _cond("create_event"),
                },
                {
                    "name": "summary",
                    "label": "Title",
                    "type": "string",
                    "placeholder": "Leave blank to keep existing",
                    "condition": _cond("update_event"),
                },
                {
                    "name": "description",
                    "label": "Description",
                    "type": "string",
                    "multiline": True,
                    "condition": _cond_any("create_event", "update_event"),
                },
                {
                    "name": "location",
                    "label": "Location",
                    "type": "string",
                    "placeholder": "Office / https://meet.google.com/...",
                    "condition": _cond_any("create_event", "update_event"),
                },
                {
                    "name": "all_day",
                    "label": "All-day event",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond_any("create_event", "update_event"),
                },
                {
                    "name": "start",
                    "label": "Start",
                    "type": "string",
                    "required": True,
                    "placeholder": "2026-06-16T10:00:00 or 2026-06-16 (all-day)",
                    "condition": _cond("create_event"),
                },
                {
                    "name": "end",
                    "label": "End",
                    "type": "string",
                    "required": True,
                    "placeholder": "2026-06-16T11:00:00 or 2026-06-17 (all-day end)",
                    "condition": _cond("create_event"),
                },
                {
                    "name": "start",
                    "label": "Start",
                    "type": "string",
                    "placeholder": "Leave blank to keep existing",
                    "condition": _cond("update_event"),
                },
                {
                    "name": "end",
                    "label": "End",
                    "type": "string",
                    "placeholder": "Leave blank to keep existing",
                    "condition": _cond("update_event"),
                },
                {
                    "name": "time_zone",
                    "label": "Time zone",
                    "type": "options",
                    "default": "",
                    "searchable": True,
                    "allowCustom": True,
                    "typeOptions": {"searchable": True, "allowCustom": True},
                    "options": _TIMEZONE_OPTIONS,
                    "description": "Leave blank to use the calendar's default time zone.",
                    "condition": _cond_any("create_event", "update_event"),
                    "mode": "advanced",
                },
                {
                    "name": "attendees",
                    "label": "Attendees",
                    "type": "string",
                    "placeholder": "alice@example.com, bob@example.com",
                    "description": "Comma-separated emails.",
                    "condition": _cond_any("create_event", "update_event"),
                },
                {
                    "name": "send_notifications",
                    "label": "Notify attendees",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond_any("create_event", "update_event", "delete_event"),
                    "mode": "advanced",
                },
                # ── list_events ─────────────────────────────────────
                {
                    "name": "query",
                    "label": "Search query",
                    "type": "string",
                    "placeholder": "team standup",
                    "condition": _cond("list_events"),
                },
                {
                    "name": "time_min",
                    "label": "Earliest start",
                    "type": "string",
                    "placeholder": "2026-06-16T00:00:00Z (defaults to now)",
                    "condition": _cond("list_events"),
                },
                {
                    "name": "time_max",
                    "label": "Latest start",
                    "type": "string",
                    "placeholder": "2026-06-23T00:00:00Z (defaults to +7 days)",
                    "condition": _cond("list_events"),
                },
                {
                    "name": "max_results",
                    "label": "Max results",
                    "type": "number",
                    "default": 25,
                    "condition": _cond("list_events"),
                },
                {
                    "name": "order_by",
                    "label": "Order by",
                    "type": "options",
                    "default": "startTime",
                    "options": [
                        {"label": "Start time", "value": "startTime"},
                        {"label": "Last updated", "value": "updated"},
                    ],
                    "condition": _cond("list_events"),
                    "mode": "advanced",
                },
                # ── quick_add ───────────────────────────────────────
                {
                    "name": "text",
                    "label": "Natural language",
                    "type": "string",
                    "required": True,
                    "placeholder": "Lunch with Sarah tomorrow at 1pm",
                    "description": (
                        "Free text parsed by Calendar's natural-language "
                        "interpreter — same engine the web UI's “quick add” uses."
                    ),
                    "condition": _cond("quick_add"),
                },
            ],
            inputs=1,
            outputs=1,
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Authorization": f"Bearer {token}"}
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Calendar API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GCalNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── operation handlers ──────────────────────────────────────────────────


def _cal_id(node: GCalNode) -> str:
    return (node.props.calendar_id or "primary").strip()


def _time_obj(value: str | None, time_zone: str | None, all_day: bool) -> dict[str, Any] | None:
    """Build a Calendar `EventDateTime` from a user-entered string. We
    accept either a full ISO 8601 timestamp or a bare `YYYY-MM-DD`
    date; `all_day=True` forces the date variant even if the user
    supplied a time component."""
    if not value:
        return None
    v = value.strip()
    is_date = all_day or (len(v) == 10 and v[4] == "-" and v[7] == "-")
    if is_date:
        return {"date": v[:10]}
    obj: dict[str, Any] = {"dateTime": v}
    if time_zone:
        obj["timeZone"] = time_zone.strip()
    return obj


def _attendee_list(csv: str | None) -> list[dict[str, str]]:
    if not csv:
        return []
    return [{"email": e.strip()} for e in csv.split(",") if e.strip()]


def _build_event_body(node: GCalNode, *, partial: bool) -> dict[str, Any]:
    """Build the JSON body for create/update. On `partial=True` only
    user-provided fields are included so update operations PATCH cleanly
    without nuking unspecified fields."""
    body: dict[str, Any] = {}
    if node.props.summary is not None and (node.props.summary or not partial):
        body["summary"] = node.props.summary
    if node.props.description is not None:
        body["description"] = node.props.description
    if node.props.location is not None:
        body["location"] = node.props.location
    start = _time_obj(node.props.start, node.props.time_zone, node.props.all_day)
    if start is not None:
        body["start"] = start
    end = _time_obj(node.props.end, node.props.time_zone, node.props.all_day)
    if end is not None:
        body["end"] = end
    attendees = _attendee_list(node.props.attendees)
    if attendees:
        body["attendees"] = attendees
    return body


async def _create_event(
    node: GCalNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    body = _build_event_body(node, partial=False)
    if "start" not in body or "end" not in body:
        return NodeResult(success=False, error="Both `start` and `end` are required.")
    params: dict[str, Any] = {}
    if node.props.send_notifications:
        params["sendUpdates"] = "all"
    resp = await client.post(
        f"{GCAL_API}/calendars/{_cal_id(node)}/events",
        headers=headers,
        params=params,
        json=body,
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


async def _update_event(
    node: GCalNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.event_id:
        return NodeResult(success=False, error="`event_id` is required.")
    body = _build_event_body(node, partial=True)
    if not body:
        return NodeResult(success=False, error="No fields supplied to update.")
    params: dict[str, Any] = {}
    if node.props.send_notifications:
        params["sendUpdates"] = "all"
    resp = await client.patch(
        f"{GCAL_API}/calendars/{_cal_id(node)}/events/{node.props.event_id}",
        headers=headers,
        params=params,
        json=body,
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


async def _delete_event(
    node: GCalNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.event_id:
        return NodeResult(success=False, error="`event_id` is required.")
    params: dict[str, Any] = {}
    if node.props.send_notifications:
        params["sendUpdates"] = "all"
    resp = await client.delete(
        f"{GCAL_API}/calendars/{_cal_id(node)}/events/{node.props.event_id}",
        headers=headers,
        params=params,
    )
    if resp.status_code not in (200, 204, 410):
        resp.raise_for_status()
    return NodeResult(
        success=True,
        output_data={"deleted": True, "event_id": node.props.event_id},
    )


async def _get_event(
    node: GCalNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.event_id:
        return NodeResult(success=False, error="`event_id` is required.")
    resp = await client.get(
        f"{GCAL_API}/calendars/{_cal_id(node)}/events/{node.props.event_id}",
        headers=headers,
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


async def _list_events(
    node: GCalNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    params: dict[str, Any] = {
        "singleEvents": "true",
        "orderBy": node.props.order_by or "startTime",
        "maxResults": max(1, min(int(node.props.max_results or 25), 2500)),
    }
    if node.props.time_min:
        params["timeMin"] = node.props.time_min.strip()
    if node.props.time_max:
        params["timeMax"] = node.props.time_max.strip()
    if node.props.query:
        params["q"] = node.props.query.strip()
    resp = await client.get(
        f"{GCAL_API}/calendars/{_cal_id(node)}/events", headers=headers, params=params
    )
    resp.raise_for_status()
    body = resp.json()
    items = body.get("items") or []
    return NodeResult(
        success=True,
        output_data={"events": items, "count": len(items)},
    )


async def _quick_add(
    node: GCalNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    text = (node.props.text or "").strip()
    if not text:
        return NodeResult(success=False, error="`text` is required for quick_add.")
    resp = await client.post(
        f"{GCAL_API}/calendars/{_cal_id(node)}/events/quickAdd",
        headers=headers,
        params={"text": text},
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


_HANDLERS = {
    "create_event": _create_event,
    "update_event": _update_event,
    "delete_event": _delete_event,
    "get_event": _get_event,
    "list_events": _list_events,
    "quick_add": _quick_add,
}
