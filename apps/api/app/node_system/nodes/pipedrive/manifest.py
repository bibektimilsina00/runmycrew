"""Pipedrive action node — manifest form.

Pipedrive's v1 REST API ships the API token as a query parameter
(`?api_token=...`), not a header. The scaffold's `query_token` auth
scheme covers this directly.

Two URL caveats:
  - The API is `https://{company_domain}.pipedrive.com/v1/...` — per-
    company subdomain. We resolve the domain from the credential.
  - Some teams use the API gateway at `https://api.pipedrive.com/v1/...`
    instead; treat the credential's `company_domain` field as the host
    fragment, defaulting to `api` for the gateway form.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_DEAL_STAGE_FIELDS = ["title", "value", "currency", "stage_id", "person_id", "org_id"]


MANIFEST = ProviderManifest(
    type="action.pipedrive",
    name="Pipedrive",
    category="integration",
    description="Pipedrive CRM — manage deals, persons, organizations, and activities.",
    icon_slug="pipedrive",
    color="#1c1c1c",
    base_url="",
    credential_type="pipedrive_api_key",
    token_field=["api_key"],
    auth="query_token",
    auth_query_param="api_token",
    fields=[
        FieldSpec(name="deal_id", label="Deal ID", type="number"),
        FieldSpec(name="person_id", label="Person ID", type="number"),
        FieldSpec(name="org_id", label="Organization ID", type="number"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="value", label="Value", type="number", mode="advanced"),
        FieldSpec(name="currency", label="Currency", type="string", default="USD", mode="advanced"),
        FieldSpec(name="stage_id", label="Stage ID", type="number", mode="advanced"),
        FieldSpec(
            name="status",
            label="Status",
            type="options",
            mode="advanced",
            options=[
                {"label": "Open", "value": "open"},
                {"label": "Won", "value": "won"},
                {"label": "Lost", "value": "lost"},
                {"label": "Deleted", "value": "deleted"},
            ],
        ),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="phone", label="Phone", type="string"),
        FieldSpec(name="term", label="Search term", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
        FieldSpec(name="start", label="Offset", type="number", default=0, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="create_deal",
            label="Create Deal",
            method="POST",
            path="https://{company_domain}.pipedrive.com/v1/deals",
            visible_fields=_DEAL_STAGE_FIELDS,
            body_fields=_DEAL_STAGE_FIELDS,
        ),
        OpSpec(
            id="get_deal",
            label="Get Deal",
            method="GET",
            path="https://{company_domain}.pipedrive.com/v1/deals/{deal_id}",
            visible_fields=["deal_id"],
        ),
        OpSpec(
            id="update_deal",
            label="Update Deal",
            method="PUT",
            path="https://{company_domain}.pipedrive.com/v1/deals/{deal_id}",
            visible_fields=["deal_id", "title", "value", "stage_id", "status"],
            body_fields=["title", "value", "stage_id", "status"],
        ),
        OpSpec(
            id="list_deals",
            label="List Deals",
            method="GET",
            path="https://{company_domain}.pipedrive.com/v1/deals",
            visible_fields=["status", "limit", "start"],
            query_fields=["status", "limit", "start"],
        ),
        OpSpec(
            id="create_person",
            label="Create Person",
            method="POST",
            path="https://{company_domain}.pipedrive.com/v1/persons",
            visible_fields=["name", "email", "phone", "org_id"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "name": getattr(v, "name", None),
                    "email": getattr(v, "email", None),
                    "phone": getattr(v, "phone", None),
                    "org_id": getattr(v, "org_id", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_person",
            label="Get Person",
            method="GET",
            path="https://{company_domain}.pipedrive.com/v1/persons/{person_id}",
            visible_fields=["person_id"],
        ),
        OpSpec(
            id="search_persons",
            label="Search Persons",
            method="GET",
            path="https://{company_domain}.pipedrive.com/v1/persons/search",
            visible_fields=["term", "limit"],
            query_fields=["term", "limit"],
        ),
        OpSpec(
            id="create_organization",
            label="Create Organization",
            method="POST",
            path="https://{company_domain}.pipedrive.com/v1/organizations",
            visible_fields=["name"],
            body_fields=["name"],
        ),
        OpSpec(
            id="list_pipelines",
            label="List Pipelines",
            method="GET",
            path="https://{company_domain}.pipedrive.com/v1/pipelines",
        ),
        OpSpec(
            id="list_stages",
            label="List Stages",
            method="GET",
            path="https://{company_domain}.pipedrive.com/v1/stages",
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "success", "type": "boolean"},
        {"label": "items", "type": "array"},
        {"label": "additional_data", "type": "object"},
    ],
    allow_error=True,
)
