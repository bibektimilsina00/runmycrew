"""Lemlist polling trigger — manifest form.

Sim ships 8 lemlist trigger events, all email delivery / engagement
events (bounced, clicked, opened, replied, sent, interested,
linkedin_replied, not_interested). Every one is a per-email event best
delivered via webhook — polling would need a scan across the whole
activities log every tick.

For polling we instead surface higher-level object events:
  - `activity_created`  — new row in the team activity log (covers
    email events at a coarse cadence)
  - `new_lead_in_campaign` — added-to-campaign observability

Not in polling (need webhooks — future 4.8):
  email_bounced, email_clicked, email_opened, email_replied,
  email_sent, interested, linkedin_replied, not_interested (all 8
  sim events).
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


def _flatten_activity(item):
    return {
        "id": item.get("_id") or item.get("id"),
        "type": item.get("type"),
        "campaign_id": item.get("campaignId"),
        "campaign_name": item.get("campaignName"),
        "lead_email": item.get("leadEmail") or item.get("email"),
        "lead_first_name": item.get("firstName"),
        "lead_last_name": item.get("lastName"),
        "date": item.get("date") or item.get("createdAt"),
    }


def _flatten_lead(item):
    return {
        "email": item.get("email"),
        "first_name": item.get("firstName"),
        "last_name": item.get("lastName"),
        "company_name": item.get("companyName"),
        "added_at": item.get("addedAt") or item.get("createdAt"),
        "campaign_id": item.get("campaignId"),
    }


register_flatten("lemlist.activity", _flatten_activity)
register_flatten("lemlist.lead", _flatten_lead)


async def _walk_lemlist(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Route by event id — activities is a top-level list, campaign
    leads is per-campaign."""
    auth_headers, _ = build_auth(
        token=token,
        scheme="basic",
        header_name="Authorization",
        value_template="",
        query_param="",
        basic_username="",
    )
    headers = {**auth_headers, "Accept": "application/json"}
    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 100))
    except (TypeError, ValueError):
        limit = 25

    if event.id == "activity_created":
        params = {"limit": limit, "page": 1}
        campaign_id = resolve_template("{campaign_id}", props) or ""
        if campaign_id:
            params["campaignId"] = campaign_id
        resp = await client.get(
            f"{manifest.base_url}/activities",
            headers=headers,
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json() or []
        return body if isinstance(body, list) else (body.get("activities") or [])

    if event.id == "new_lead_in_campaign":
        campaign_id = resolve_template("{campaign_id}", props) or ""
        if not campaign_id:
            return []
        resp = await client.get(
            f"{manifest.base_url}/campaigns/{campaign_id}/export/leads",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json() or []
        # Lemlist returns leads as an array of objects directly.
        leads = body if isinstance(body, list) else (body.get("leads") or [])
        # Stamp campaign_id onto each lead so the flatten can hoist it.
        for lead in leads:
            if isinstance(lead, dict):
                lead["campaignId"] = campaign_id
                # Use email as stable id — Lemlist leads have no
                # explicit primary key on this endpoint.
                if lead.get("email") and not lead.get("id"):
                    lead["id"] = lead["email"]
        return leads

    return []


MANIFEST = PollingTriggerManifest(
    type="trigger.lemlist",
    name="Lemlist",
    description=(
        "Poll Lemlist for new activities (email events at coarse cadence) "
        "or new leads added to a campaign. For real-time email events, "
        "attach a Lemlist webhook instead."
    ),
    icon_slug="lemlist",
    color="#1c1c1c",
    base_url="https://api.lemlist.com/api",
    credential_type="lemlist_api_key",
    token_field=["api_key"],
    auth="basic",
    provider="lemlist",
    default_poll_interval_seconds=90,
    common_fields=[
        FieldSpec(
            name="campaign_id",
            label="Campaign ID (required for lead events; optional for activities)",
            type="string",
        ),
    ],
    events=[
        PollingEvent(
            id="activity_created",
            label="New Activity",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="lemlist.activity",
        ),
        PollingEvent(
            id="new_lead_in_campaign",
            label="New Lead Added to Campaign",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="lemlist.lead",
            extra_fields=["campaign_id"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "type", "type": "string"},
        {"label": "campaign_id", "type": "string"},
        {"label": "lead_email", "type": "string"},
        {"label": "first_name", "type": "string"},
        {"label": "date", "type": "string"},
    ],
    paginate_fn=_walk_lemlist,
)
