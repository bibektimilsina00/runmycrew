"""Enrichment.io action node — Enrichment — contact + company data-as-a-service.

REST at https://api.enrichment.io/v1. See sim-parity roadmap §4.15.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.enrichment",
    name="Enrichment.io",
    category="integration",
    description="Enrichment — contact + company data-as-a-service.",
    icon_slug="enrichment",
    color="#1c1c1c",
    base_url="https://api.enrichment.io/v1",
    credential_type="enrichment_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="linkedin_url", label="LinkedIn URL", type="string"),
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="company", label="Company Name", type="string"),
    ],
    operations=[
        OpSpec(
            id="enrich_contact",
            label="Enrich Contact",
            method="POST",
            path="/contact/enrich",
            visible_fields=["email", "linkedin_url"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None) or None,
                    "linkedin_url": getattr(v, "linkedin_url", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="enrich_company",
            label="Enrich Company",
            method="POST",
            path="/company/enrich",
            visible_fields=["domain"],
            body_builder=lambda v: {"domain": getattr(v, "domain", "") or ""},
        ),
        OpSpec(
            id="verify_email",
            label="Verify Email",
            method="POST",
            path="/email/verify",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
