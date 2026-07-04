"""Lemlist action node — manifest form.

Lemlist REST API at `https://api.lemlist.com/api/`. Basic auth using
`Basic base64(:api_key)` — empty username, api_key as password. The
scaffold's `basic` scheme with `basic_username=""` (default) produces
exactly that shape.

7 ops cover the typical outbound-email workflow:
list_campaigns, get_campaign, list_leads_in_campaign,
add_lead_to_campaign, delete_lead, pause_lead, get_team_activities.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.lemlist",
    name="Lemlist",
    category="integration",
    description="Lemlist — outbound email campaigns, leads, activities.",
    icon_slug="lemlist",
    color="#1c1c1c",
    base_url="https://api.lemlist.com/api",
    credential_type="lemlist_api_key",
    token_field=["api_key"],
    auth="basic",
    # Empty username → `Basic base64(:api_key)`, lemlist's convention.
    auth_basic_username="",
    fields=[
        FieldSpec(name="campaign_id", label="Campaign ID", type="string"),
        FieldSpec(name="lead_email", label="Lead Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="company_name", label="Company Name", type="string"),
        FieldSpec(name="icebreaker", label="Icebreaker", type="string", mode="advanced"),
        FieldSpec(name="phone", label="Phone", type="string", mode="advanced"),
        FieldSpec(name="linkedin_url", label="LinkedIn URL", type="string", mode="advanced"),
        FieldSpec(
            name="deduplicate",
            label="Deduplicate (skip if lead exists)",
            type="boolean",
            default=True,
            mode="advanced",
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_campaigns",
            label="List Campaigns",
            method="GET",
            path="/campaigns",
            visible_fields=["limit", "page"],
            query_builder=lambda v: {
                "limit": int(getattr(v, "limit", 100) or 100),
                "page": int(getattr(v, "page", 1) or 1),
            },
        ),
        OpSpec(
            id="get_campaign",
            label="Get Campaign",
            method="GET",
            path="/campaigns/{campaign_id}",
            visible_fields=["campaign_id"],
        ),
        OpSpec(
            id="list_leads_in_campaign",
            label="List Leads in Campaign",
            method="GET",
            path="/campaigns/{campaign_id}/export/leads",
            visible_fields=["campaign_id"],
        ),
        OpSpec(
            id="add_lead_to_campaign",
            label="Add Lead to Campaign",
            method="POST",
            path="/campaigns/{campaign_id}/leads/{lead_email}",
            visible_fields=[
                "campaign_id",
                "lead_email",
                "first_name",
                "last_name",
                "company_name",
                "icebreaker",
                "phone",
                "linkedin_url",
                "deduplicate",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "firstName": getattr(v, "first_name", None) or None,
                    "lastName": getattr(v, "last_name", None) or None,
                    "companyName": getattr(v, "company_name", None) or None,
                    "icebreaker": getattr(v, "icebreaker", None) or None,
                    "phone": getattr(v, "phone", None) or None,
                    "linkedinUrl": getattr(v, "linkedin_url", None) or None,
                }.items()
                if val
            },
            query_builder=lambda v: (
                {"deduplicate": "true"} if getattr(v, "deduplicate", True) else {}
            ),
        ),
        OpSpec(
            id="delete_lead_from_campaign",
            label="Delete Lead from Campaign",
            method="DELETE",
            path="/campaigns/{campaign_id}/leads/{lead_email}",
            visible_fields=["campaign_id", "lead_email"],
        ),
        OpSpec(
            id="pause_lead",
            label="Pause Lead in Campaign",
            method="POST",
            path="/campaigns/{campaign_id}/leads/{lead_email}/pause",
            visible_fields=["campaign_id", "lead_email"],
        ),
        OpSpec(
            id="list_activities",
            label="List Team Activities",
            method="GET",
            path="/activities",
            visible_fields=["campaign_id", "limit", "page"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "campaignId": getattr(v, "campaign_id", None) or None,
                    "limit": int(getattr(v, "limit", 100) or 100),
                    "page": int(getattr(v, "page", 1) or 1),
                }.items()
                if val is not None
            },
        ),
    ],
    outputs_schema=[
        {"label": "_id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "campaigns", "type": "array"},
        {"label": "leads", "type": "array"},
    ],
    allow_error=True,
)
