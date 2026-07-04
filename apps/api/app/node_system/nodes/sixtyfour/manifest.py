"""SixtyFour action node — SixtyFour — AI research for lead enrichment.

REST at https://api.sixtyfour.ai/v1. See sim-parity roadmap Phase 4.16/4.17.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.sixtyfour",
    name="SixtyFour",
    category="integration",
    description="SixtyFour — AI research for lead enrichment.",
    icon_slug="sixtyfour",
    color="#1c1c1c",
    base_url="https://api.sixtyfour.ai/v1",
    credential_type="sixtyfour_api_key",
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
            id="enrich_lead",
            label="Enrich Lead",
            method="POST",
            path="/enrich-lead",
            visible_fields=["email", "linkedin_url", "company"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None) or None,
                    "linkedin_url": getattr(v, "linkedin_url", None) or None,
                    "company": getattr(v, "company", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="enrich_company",
            label="Enrich Company",
            method="POST",
            path="/enrich-company",
            visible_fields=["domain"],
            body_builder=lambda v: {"domain": getattr(v, "domain", "") or ""},
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
