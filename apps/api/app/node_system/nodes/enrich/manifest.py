"""Enrich.so action node — Enrich.so — LinkedIn scraper + email finder.

REST at https://api.enrich.so/v1. See sim-parity roadmap §4.15.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.enrich",
    name="Enrich.so",
    category="integration",
    description="Enrich.so — LinkedIn scraper + email finder.",
    icon_slug="enrich",
    color="#1c1c1c",
    base_url="https://api.enrich.so/v1",
    credential_type="enrich_api_key",
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
            id="person_by_linkedin",
            label="Person by LinkedIn URL",
            method="POST",
            path="/person",
            visible_fields=["linkedin_url"],
            body_builder=lambda v: {"linkedin_url": getattr(v, "linkedin_url", "") or ""},
        ),
        OpSpec(
            id="person_by_email",
            label="Person by Email",
            method="POST",
            path="/person",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        OpSpec(
            id="company_by_domain",
            label="Company by Domain",
            method="POST",
            path="/company",
            visible_fields=["domain"],
            body_builder=lambda v: {"domain": getattr(v, "domain", "") or ""},
        ),
        OpSpec(
            id="email_finder",
            label="Email Finder",
            method="POST",
            path="/email-finder",
            visible_fields=["first_name", "last_name", "domain"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                    "domain": getattr(v, "domain", None) or None,
                }.items()
                if val is not None
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
