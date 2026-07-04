"""Persona action node — Persona — identity verification + KYC.

REST at https://api.withpersona.com/api/v1. See sim-parity roadmap Phase 4.16/4.17.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.persona",
    name="Persona",
    category="integration",
    description="Persona — identity verification + KYC.",
    icon_slug="persona",
    color="#1c1c1c",
    base_url="https://api.withpersona.com/api/v1",
    credential_type="persona_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="linkedin_url", label="LinkedIn URL", type="string"),
        FieldSpec(name="domain", label="Domain / Website", type="string"),
        FieldSpec(name="company", label="Company Name", type="string"),
        FieldSpec(name="query", label="Search Query (JSON)", type="json", mode="advanced"),
        FieldSpec(name="size", label="Size", type="number", default=25, mode="advanced"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
        FieldSpec(name="per_page", label="Per Page", type="number", default=25, mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
        FieldSpec(name="inquiry_id", label="Inquiry ID", type="string"),
        FieldSpec(name="verification_id", label="Verification ID", type="string"),
        FieldSpec(name="account_id", label="Account ID", type="string"),
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="start_date", label="Start Date (YYYY-MM)", type="string"),
        FieldSpec(name="end_date", label="End Date (YYYY-MM)", type="string"),
    ],
    operations=[
        OpSpec(
            id="get_inquiry",
            label="Get Inquiry",
            method="GET",
            path="/inquiries/{inquiry_id}",
            visible_fields=["inquiry_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_inquiries",
            label="List Inquiries",
            method="GET",
            path="/inquiries",
            visible_fields=["page", "per_page"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "page[size]": int(getattr(v, "per_page", 25) or 25),
                    "page[number]": int(getattr(v, "page", 1) or 1),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_verification",
            label="Get Verification",
            method="GET",
            path="/verifications/{verification_id}",
            visible_fields=["verification_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_account",
            label="Get Account",
            method="GET",
            path="/accounts/{account_id}",
            visible_fields=["account_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "result", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
