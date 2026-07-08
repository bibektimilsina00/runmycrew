"""Enrow action node — Enrow — waterfall B2B email finder + verifier.

REST at https://api.enrow.io/v1. See sim-parity roadmap §4.15.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.enrow",
    name="Enrow",
    category="integration",
    description="Enrow — waterfall B2B email finder + verifier.",
    icon_slug="enrow",
    color="#ffffff",
    base_url="https://api.enrow.io/v1",
    credential_type="enrow_api_key",
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
            id="find_email",
            label="Find Email",
            method="POST",
            path="/find-email",
            visible_fields=["first_name", "last_name", "domain", "company"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                    "domain": getattr(v, "domain", None) or None,
                    "company": getattr(v, "company", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="verify_email",
            label="Verify Email",
            method="POST",
            path="/verify-email",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        OpSpec(
            id="enrich_contact",
            label="Enrich Contact",
            method="POST",
            path="/enrich",
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
