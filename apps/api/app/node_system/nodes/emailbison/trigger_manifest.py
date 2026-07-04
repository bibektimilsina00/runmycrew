"""Emailbison polling trigger — manifest form.

2 poll-observable events. The remaining 15 sim events are per-email
delivery events (bounced/opened/clicked/replied/sent/etc.) that fit
webhook delivery, not polling — deferred to a future 4.9 webhook batch.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_lead(item):
    return {
        "id": item.get("id"),
        "email": item.get("email"),
        "first_name": item.get("first_name"),
        "last_name": item.get("last_name"),
        "company_name": item.get("company_name"),
        "title": item.get("title"),
        "campaign_id": item.get("campaign_id"),
        "status": item.get("status"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def _flatten_campaign(item):
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "status": item.get("status"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "workspace_id": item.get("workspace_id"),
    }


register_flatten("emailbison.lead", _flatten_lead)
register_flatten("emailbison.campaign", _flatten_campaign)


MANIFEST = PollingTriggerManifest(
    type="trigger.emailbison",
    name="Emailbison",
    description=(
        "Poll Emailbison for new leads (workspace-wide or per-campaign) "
        "and new campaigns. Per-delivery email events require a webhook."
    ),
    icon_slug="emailbison",
    color="#1c1c1c",
    base_url="https://api.emailbison.com/api/v1",
    credential_type="emailbison_api_key",
    token_field=["api_key"],
    auth="bearer",
    provider="emailbison",
    default_poll_interval_seconds=90,
    common_fields=[
        FieldSpec(
            name="campaign_id",
            label="Campaign ID (optional; blank = workspace-wide leads)",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="per_page",
            label="Per page",
            type="number",
            default=50,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_lead",
            label="New Lead",
            list_path="/leads",
            list_params={"per_page": "{per_page}", "campaign_id": "{campaign_id}"},
            strategy="known_ids",
            id_field="id",
            flatten="emailbison.lead",
        ),
        PollingEvent(
            id="new_campaign",
            label="New Campaign",
            list_path="/campaigns",
            list_params={"per_page": "{per_page}"},
            strategy="known_ids",
            id_field="id",
            flatten="emailbison.campaign",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "campaign_id", "type": "string"},
        {"label": "created_at", "type": "string"},
    ],
)
