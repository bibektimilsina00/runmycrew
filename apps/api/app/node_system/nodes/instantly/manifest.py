"""Instantly action node — manifest form.

Instantly.ai is a cold-outreach campaign tool. v2 API lives at
`https://api.instantly.ai/api/v2` with Bearer auth. We expose the
campaign-management + lead-flow ops the typical workflow needs:

  - Create / list / pause campaigns
  - Add leads to a campaign
  - Get lead status
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.instantly",
    name="Instantly",
    category="integration",
    description="Cold-email outreach campaigns + lead management via Instantly.ai.",
    icon_slug="instantly",
    color="#1c1c1c",
    base_url="https://api.instantly.ai/api/v2",
    credential_type="instantly_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="campaign_id", label="Campaign ID", type="string"),
        FieldSpec(name="lead_id", label="Lead ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string", mode="advanced"),
        FieldSpec(name="last_name", label="Last Name", type="string", mode="advanced"),
        FieldSpec(name="company_name", label="Company", type="string", mode="advanced"),
        FieldSpec(name="personalization", label="Personalization", type="string", mode="advanced"),
        FieldSpec(
            name="custom_variables", label="Custom Variables (JSON)", type="json", mode="advanced"
        ),
        FieldSpec(name="name", label="Campaign Name", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_campaigns",
            label="List Campaigns",
            method="GET",
            path="/campaigns",
            visible_fields=["limit"],
            query_fields=["limit"],
        ),
        OpSpec(
            id="create_campaign",
            label="Create Campaign",
            method="POST",
            path="/campaigns",
            visible_fields=["name"],
            body_fields=["name"],
        ),
        OpSpec(
            id="get_campaign",
            label="Get Campaign",
            method="GET",
            path="/campaigns/{campaign_id}",
            visible_fields=["campaign_id"],
        ),
        OpSpec(
            id="pause_campaign",
            label="Pause Campaign",
            method="POST",
            path="/campaigns/{campaign_id}/pause",
            visible_fields=["campaign_id"],
        ),
        OpSpec(
            id="resume_campaign",
            label="Resume Campaign",
            method="POST",
            path="/campaigns/{campaign_id}/resume",
            visible_fields=["campaign_id"],
        ),
        OpSpec(
            id="add_lead",
            label="Add Lead",
            method="POST",
            path="/leads",
            visible_fields=[
                "campaign_id",
                "email",
                "first_name",
                "last_name",
                "company_name",
                "personalization",
                "custom_variables",
            ],
            body_fields=[
                "campaign_id",
                "email",
                "first_name",
                "last_name",
                "company_name",
                "personalization",
                "custom_variables",
            ],
        ),
        OpSpec(
            id="get_lead",
            label="Get Lead",
            method="GET",
            path="/leads/{lead_id}",
            visible_fields=["lead_id"],
        ),
        OpSpec(
            id="list_leads",
            label="List Leads",
            method="GET",
            path="/leads",
            visible_fields=["campaign_id", "limit"],
            query_fields=["campaign_id", "limit"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "items", "type": "array"},
        {"label": "campaign_id", "type": "string"},
    ],
    allow_error=True,
)
