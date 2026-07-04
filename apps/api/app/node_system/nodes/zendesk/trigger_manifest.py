"""Zendesk polling trigger — manifest form.

Watches a Zendesk instance for new / updated tickets + new users.
Zendesk hosts each customer on `{subdomain}.zendesk.com` — the
subdomain lives in the credential, so we drop down to a custom
paginate_fn that builds the URL and Basic auth header itself.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_ticket(item):
    return {
        "id": item.get("id"),
        "subject": item.get("subject"),
        "description": item.get("description"),
        "status": item.get("status"),
        "priority": item.get("priority"),
        "requester_id": item.get("requester_id"),
        "assignee_id": item.get("assignee_id"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "url": item.get("url"),
        "tags": item.get("tags"),
    }


def _flatten_user(item):
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "email": item.get("email"),
        "role": item.get("role"),
        "organization_id": item.get("organization_id"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


register_flatten("zendesk.ticket", _flatten_ticket)
register_flatten("zendesk.user", _flatten_user)


async def _walk_zendesk(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Build the Zendesk URL from credential.subdomain + Basic auth
    (`{email}/token:{api_key}`). Response body wraps items under
    `tickets` / `users` — pull the right key by event id."""
    cred = getattr(props, "_cred", None) or {}
    subdomain = str(cred.get("subdomain") or "").strip()
    email = str(cred.get("email") or "").strip()
    api_key = token or str(cred.get("api_key") or "")
    if not subdomain or not email or not api_key:
        return []
    base = f"https://{subdomain}.zendesk.com/api/v2"
    endpoint = event.list_path.lstrip("/")
    url = f"{base}/{endpoint}"
    encoded = base64.b64encode(f"{email}/token:{api_key}".encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
    }
    params: dict[str, Any] = {}
    for k, v in (event.list_params or {}).items():
        params[k] = v if not isinstance(v, str) else v
    resp = await client.get(url, headers=headers, params=params or None, timeout=30)
    resp.raise_for_status()
    payload = resp.json() or {}
    # The wrap key varies per endpoint — tickets.json → 'tickets',
    # users.json → 'users'. Fall back to the first list value.
    for key in ("tickets", "users", "results"):
        if isinstance(payload.get(key), list):
            return payload[key]
    for v in payload.values():
        if isinstance(v, list):
            return v
    return []


MANIFEST = PollingTriggerManifest(
    type="trigger.zendesk",
    name="Zendesk",
    description="Poll Zendesk for new / updated tickets or new users.",
    icon_slug="zendesk",
    color="#1c1c1c",
    base_url="",  # unused — paginate_fn builds the URL from credential
    credential_type="zendesk_api_key",
    token_field=["api_key"],
    auth="none",
    provider="zendesk",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="per_page",
            label="Per Page",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_ticket",
            label="New Ticket",
            list_path="/tickets.json",
            list_params={"sort_by": "created_at", "sort_order": "desc"},
            strategy="known_ids",
            id_field="id",
            flatten="zendesk.ticket",
        ),
        PollingEvent(
            id="updated_ticket",
            label="Ticket Updated",
            list_path="/tickets.json",
            list_params={"sort_by": "updated_at", "sort_order": "desc"},
            strategy="since_timestamp",
            timestamp_field="updated_at",
            flatten="zendesk.ticket",
        ),
        PollingEvent(
            id="new_user",
            label="New User",
            list_path="/users.json",
            list_params={"role": "end-user"},
            strategy="known_ids",
            id_field="id",
            flatten="zendesk.user",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "number"},
        {"label": "subject", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "priority", "type": "string"},
        {"label": "created_at", "type": "string"},
        {"label": "updated_at", "type": "string"},
    ],
    paginate_fn=_walk_zendesk,
)
