"""Icypeas action node — Icypeas — email finder + LinkedIn enrichment.

REST at https://app.icypeas.com/api. See sim-parity roadmap §4.15.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.icypeas",
    name="Icypeas",
    category="integration",
    description="Icypeas — email finder + LinkedIn enrichment.",
    icon_slug="icypeas",
    color="#ffffff",
    base_url="https://app.icypeas.com/api",
    credential_type="icypeas_api_key",
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
            id="email_search",
            label="Email Search (single)",
            method="POST",
            path="/email-search",
            visible_fields=["first_name", "last_name", "domain"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "firstname": getattr(v, "first_name", None) or None,
                    "lastname": getattr(v, "last_name", None) or None,
                    "domainOrCompany": getattr(v, "domain", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="email_verification",
            label="Email Verification",
            method="POST",
            path="/email-verification",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        OpSpec(
            id="linkedin_enrich",
            label="LinkedIn Enrichment",
            method="POST",
            path="/linkedin-search",
            visible_fields=["linkedin_url"],
            body_builder=lambda v: {"linkedinurl": getattr(v, "linkedin_url", "") or ""},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
