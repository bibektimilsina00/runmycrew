"""Instantly polling trigger — manifest form.

Instantly v2 API at `https://api.instantly.ai/api/v2`. Bearer auth.
Leads list is POST-only (filter body), so we drop down to a custom
paginate_fn.

Events (3 poll-observable of sims 19):
  - `new_lead`               — known_ids on lead id
  - `lead_status_changed`    — custom diff tracking {lead_id: status}.
    Covers sim's lead_interested / lead_meeting_booked /
    lead_unsubscribed / lead_not_interested / lead_out_of_office /
    lead_closed / lead_neutral / lead_no_show / lead_wrong_person /
    lead_meeting_completed transitions — the payload includes the
    new status, so downstream can gate on it.
  - `campaign_completed`     — custom diff on campaigns.status
                               transitioning to "completed" (status=3)

Not in polling (need webhooks — future 4.9):
  email_bounced, email_opened, email_sent, link_clicked, reply_received,
  auto_reply_received, account_error — per-delivery events, webhook-only.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.nodes.instantly import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)

_INSTANTLY_API = "https://api.instantly.ai/api/v2"


def _flatten_lead(item):
    return {
        "id": item.get("id"),
        "email": item.get("email"),
        "first_name": item.get("first_name"),
        "last_name": item.get("last_name"),
        "company_name": item.get("company_name"),
        "status": item.get("status"),
        "campaign_id": item.get("campaign"),
        "created_at": item.get("timestamp_created"),
        "updated_at": item.get("timestamp_updated"),
        "email_opened": item.get("email_opened"),
        "email_clicked": item.get("email_clicked"),
        "email_replied": item.get("email_replied"),
    }


def _flatten_campaign(item):
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "status": item.get("status"),
        "created_at": item.get("timestamp_created"),
        "updated_at": item.get("timestamp_updated"),
        "sequences": item.get("sequences"),
    }


register_flatten("instantly.lead", _flatten_lead)
register_flatten("instantly.campaign", _flatten_campaign)


def _diff_lead_status_change(items, cursor, props, event_id):
    """Fire when a lead's status changes between polls. Cursor tracks
    `{lead_id: status_int}`; first poll snapshots silent."""
    campaign_id = str(getattr(props, "campaign_id", "") or "")
    prior = None
    if (
        isinstance(cursor, dict)
        and cursor.get("event_type") == event_id
        and cursor.get("campaign_id") == campaign_id
    ):
        prior = cursor.get("statuses")
        if not isinstance(prior, dict):
            prior = None

    new_statuses: dict[str, Any] = {}
    matches: list[dict[str, Any]] = []
    first_poll = prior is None
    for item in items:
        lead_id = str(item.get("id") or "")
        if not lead_id:
            continue
        status = item.get("status")
        new_statuses[lead_id] = status
        if first_poll:
            continue
        prev = prior.get(lead_id) if isinstance(prior, dict) else None
        if prev is not None and prev != status:
            flat = _flatten_lead(item)
            flat["event_type"] = event_id
            flat["change"] = {"key": "status", "from": prev, "to": status}
            matches.append(flat)
    return matches, {
        "event_type": event_id,
        "campaign_id": campaign_id,
        "statuses": new_statuses,
    }


def _diff_campaign_completed(items, cursor, props, event_id):
    """Fire when a campaign transitions to status=3 (completed).
    Cursor tracks {campaign_id: prior_status}. Instantly's campaign
    status enum: 1=active, 2=paused, 3=completed, 4=draft."""
    prior = None
    if isinstance(cursor, dict) and cursor.get("event_type") == event_id:
        prior = cursor.get("statuses")
        if not isinstance(prior, dict):
            prior = None

    new_statuses: dict[str, Any] = {}
    matches: list[dict[str, Any]] = []
    first_poll = prior is None
    for item in items:
        cid = str(item.get("id") or "")
        if not cid:
            continue
        status = item.get("status")
        new_statuses[cid] = status
        if first_poll:
            continue
        prev = prior.get(cid) if isinstance(prior, dict) else None
        # Emit only when transitioning INTO completed. If it was
        # already completed, don't re-fire.
        if prev != status and status == 3:
            flat = _flatten_campaign(item)
            flat["event_type"] = event_id
            matches.append(flat)
    return matches, {"event_type": event_id, "statuses": new_statuses}


async def _walk_instantly(
    client: httpx.AsyncClient,
    *,
    manifest,  # noqa: ARG001
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Route by event id. leads.list is POST; campaigns.list is GET
    with query params."""
    headers = {
        "Authorization": f"Bearer {token or ''}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 100))
    except (TypeError, ValueError):
        limit = 25

    if event.id in ("new_lead", "lead_status_changed"):
        campaign_id = str(getattr(props, "campaign_id", "") or "")
        body: dict[str, Any] = {"limit": limit}
        if campaign_id:
            body["campaign"] = campaign_id
        resp = await client.post(
            f"{_INSTANTLY_API}/leads/list",
            headers=headers,
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("items") or payload.get("data") or []

    if event.id == "campaign_completed":
        resp = await client.get(
            f"{_INSTANTLY_API}/campaigns",
            headers=headers,
            params={"limit": limit},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("items") or payload.get("data") or []

    return []


MANIFEST = PollingTriggerManifest(
    type="trigger.instantly",
    name=NAME,
    description=(
        "Poll Instantly for new leads, lead status changes (interested / "
        "meeting_booked / unsubscribed / …), or completed campaigns. For "
        "per-delivery email events attach an Instantly webhook."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url=_INSTANTLY_API,
    credential_type="instantly_api_key",
    token_field=["api_key"],
    auth="bearer",
    provider="instantly",
    default_poll_interval_seconds=90,
    common_fields=[
        FieldSpec(
            name="campaign_id",
            label="Campaign ID (optional; blank = all campaigns)",
            type="string",
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_lead",
            label="New Lead",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="instantly.lead",
        ),
        PollingEvent(
            id="lead_status_changed",
            label="Lead Status Changed",
            list_path="",
            diff_handler=_diff_lead_status_change,
        ),
        PollingEvent(
            id="campaign_completed",
            label="Campaign Completed",
            list_path="",
            diff_handler=_diff_campaign_completed,
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "campaign_id", "type": "string"},
        {"label": "change", "type": "object"},
        {"label": "name", "type": "string"},
    ],
    paginate_fn=_walk_instantly,
)
