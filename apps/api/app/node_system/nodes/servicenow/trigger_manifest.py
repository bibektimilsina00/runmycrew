"""ServiceNow polling trigger — manifest form.

ServiceNow Table API at `https://{instance}.service-now.com/api/now/table/{table}`.
Basic auth via the same `{username}:{api_key}` shape as the action node.
Instance lives on the credential — no static base_url, so a custom
paginate_fn builds the URL per-poll.

Events (all 4 sim events — every one is poll-observable):
  - `incident_created`         — known_ids on incident sys_id
  - `incident_updated`         — since_timestamp on sys_updated_on
  - `change_request_created`   — known_ids on change_request sys_id
  - `change_request_updated`   — since_timestamp on sys_updated_on

Note: ServiceNow's sys_updated_on is a naive UTC timestamp
("2026-07-04 12:34:56") — the scaffold's since_timestamp diff sorts
lexicographically, which produces correct ordering for that format.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    build_auth,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template


def _pull_ref(field: Any) -> str:
    """ServiceNow returns reference fields as either a bare sys_id or
    an object like `{value, link, display_value}` (depending on
    sysparm_display_value). Normalize to the display string."""
    if isinstance(field, dict):
        return str(field.get("display_value") or field.get("value") or "")
    return str(field or "")


def _flatten_incident(item):
    return {
        "sys_id": item.get("sys_id"),
        "number": item.get("number"),
        "short_description": item.get("short_description"),
        "description": item.get("description"),
        "state": _pull_ref(item.get("state")),
        "priority": _pull_ref(item.get("priority")),
        "urgency": _pull_ref(item.get("urgency")),
        "assignment_group": _pull_ref(item.get("assignment_group")),
        "assigned_to": _pull_ref(item.get("assigned_to")),
        "caller_id": _pull_ref(item.get("caller_id")),
        "category": _pull_ref(item.get("category")),
        "opened_at": item.get("opened_at"),
        "sys_created_on": item.get("sys_created_on"),
        "sys_updated_on": item.get("sys_updated_on"),
    }


def _flatten_change(item):
    return {
        "sys_id": item.get("sys_id"),
        "number": item.get("number"),
        "short_description": item.get("short_description"),
        "description": item.get("description"),
        "state": _pull_ref(item.get("state")),
        "priority": _pull_ref(item.get("priority")),
        "risk": _pull_ref(item.get("risk")),
        "type": _pull_ref(item.get("type")),
        "assignment_group": _pull_ref(item.get("assignment_group")),
        "assigned_to": _pull_ref(item.get("assigned_to")),
        "requested_by": _pull_ref(item.get("requested_by")),
        "start_date": item.get("start_date"),
        "end_date": item.get("end_date"),
        "sys_created_on": item.get("sys_created_on"),
        "sys_updated_on": item.get("sys_updated_on"),
    }


register_flatten("servicenow.incident", _flatten_incident)
register_flatten("servicenow.change_request", _flatten_change)


async def _walk_servicenow(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Route by event id → table + sort. Reads instance + username
    from the credential dict."""
    cred = getattr(props, "_cred", None) or {}
    instance = str(cred.get("instance") or "").strip()
    username = str(cred.get("username") or "")
    if not instance or not username or not token:
        return []
    base = f"https://{instance}.service-now.com/api/now"

    table = "incident" if "incident" in event.id else "change_request"
    order = "^ORDERBYDESCsys_updated_on" if "updated" in event.id else "^ORDERBYDESCsys_created_on"
    extra_query = resolve_template("{query}", props) or ""
    sysparm_query = (extra_query + order) if extra_query else order.lstrip("^")

    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 250))
    except (TypeError, ValueError):
        limit = 25

    auth_headers, _ = build_auth(
        token=token,
        scheme="basic",
        header_name="Authorization",
        value_template="",
        query_param="",
        basic_username=username,
    )
    headers = {**auth_headers, "Accept": "application/json"}
    params = {
        "sysparm_query": sysparm_query,
        "sysparm_limit": limit,
        "sysparm_display_value": "true",
    }
    resp = await client.get(
        f"{base}/table/{table}",
        headers=headers,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json() or {}
    items = body.get("result") or []
    # Hoist sys_updated_on → updated so since_timestamp diff can key
    # on it. sys_id → id so the known_ids diff can too.
    for item in items:
        if item.get("sys_updated_on"):
            item["updated"] = item["sys_updated_on"]
        if item.get("sys_id"):
            item["id"] = item["sys_id"]
    return items


MANIFEST = PollingTriggerManifest(
    type="trigger.servicenow",
    name="ServiceNow",
    description=(
        "Poll ServiceNow for new / updated incidents or change requests. "
        "Basic auth via username + password/token."
    ),
    icon_slug="servicenow",
    color="#1c1c1c",
    base_url="",
    credential_type="servicenow_api_key",
    token_field=["api_key"],
    auth="basic",
    provider="servicenow",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="query",
            label="Extra encoded query (prepended; blank = watch everything)",
            type="string",
            mode="advanced",
            placeholder="active=true^priority=1",
        ),
    ],
    events=[
        PollingEvent(
            id="incident_created",
            label="Incident Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="servicenow.incident",
        ),
        PollingEvent(
            id="incident_updated",
            label="Incident Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="servicenow.incident",
        ),
        PollingEvent(
            id="change_request_created",
            label="Change Request Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="servicenow.change_request",
        ),
        PollingEvent(
            id="change_request_updated",
            label="Change Request Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="servicenow.change_request",
        ),
    ],
    outputs_schema=[
        {"label": "sys_id", "type": "string"},
        {"label": "number", "type": "string"},
        {"label": "short_description", "type": "string"},
        {"label": "state", "type": "string"},
        {"label": "priority", "type": "string"},
        {"label": "assigned_to", "type": "string"},
        {"label": "sys_created_on", "type": "string"},
        {"label": "sys_updated_on", "type": "string"},
    ],
    paginate_fn=_walk_servicenow,
)
