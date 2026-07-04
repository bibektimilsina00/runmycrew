"""Emailbison action node — manifest form.

Emailbison v1 API at `https://api.emailbison.com/api/v1`. Bearer auth
via API key from workspace settings.

5 ops cover the typical outbound-email workflow: list/get campaigns,
list/create leads, and update a lead's contact fields.

Note: emailbison's per-delivery events (email_bounced, email_opened,
email_clicked, reply_received, etc. — sim ships 17 events) are best
served by webhook, not polling. This action node handles CRUD; the
trigger surfaces new_lead + new_campaign at a coarse cadence.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.emailbison",
    name="Emailbison",
    category="integration",
    description="Emailbison — outbound-email campaigns, leads, workspaces.",
    icon_slug="emailbison",
    color="#1c1c1c",
    base_url="https://api.emailbison.com/api/v1",
    credential_type="emailbison_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="campaign_id", label="Campaign ID", type="string"),
        FieldSpec(name="lead_id", label="Lead ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="company_name", label="Company Name", type="string"),
        FieldSpec(name="title", label="Job Title", type="string", mode="advanced"),
        FieldSpec(
            name="custom_fields",
            label="Custom Fields (JSON)",
            type="json",
            mode="advanced",
        ),
        FieldSpec(name="limit", label="Per page", type="number", default=25, mode="advanced"),
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
                "per_page": int(getattr(v, "limit", 25) or 25),
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
            id="list_leads",
            label="List Leads",
            method="GET",
            path="/leads",
            visible_fields=["campaign_id", "limit", "page"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "campaign_id": getattr(v, "campaign_id", None) or None,
                    "per_page": int(getattr(v, "limit", 25) or 25),
                    "page": int(getattr(v, "page", 1) or 1),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="create_lead",
            label="Create Lead",
            method="POST",
            path="/leads",
            visible_fields=[
                "campaign_id",
                "email",
                "first_name",
                "last_name",
                "company_name",
                "title",
                "custom_fields",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "campaign_id": getattr(v, "campaign_id", None) or None,
                    "email": getattr(v, "email", None) or None,
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                    "company_name": getattr(v, "company_name", None) or None,
                    "title": getattr(v, "title", None) or None,
                    "custom_fields": getattr(v, "custom_fields", None) or None,
                }.items()
                if val
            },
        ),
        OpSpec(
            id="update_lead",
            label="Update Lead",
            method="PATCH",
            path="/leads/{lead_id}",
            visible_fields=[
                "lead_id",
                "email",
                "first_name",
                "last_name",
                "company_name",
                "title",
                "custom_fields",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None) or None,
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                    "company_name": getattr(v, "company_name", None) or None,
                    "title": getattr(v, "title", None) or None,
                    "custom_fields": getattr(v, "custom_fields", None) or None,
                }.items()
                if val
            },
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "campaigns", "type": "array"},
        {"label": "leads", "type": "array"},
    ],
    allow_error=True,
)
