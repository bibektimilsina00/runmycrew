"""Findymail action node — email finder + LinkedIn lookup.

REST at https://app.findymail.com/api. Bearer auth.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.findymail",
    name="Findymail",
    category="integration",
    description="Findymail — find + verify B2B emails by name, domain, or LinkedIn URL.",
    icon_slug="findymail",
    color="#1c1c1c",
    base_url="https://app.findymail.com/api",
    credential_type="findymail_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="name", label="Full Name", type="string"),
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="linkedin_url", label="LinkedIn URL", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
    ],
    operations=[
        OpSpec(
            id="find_email_from_name",
            label="Find Email from Name",
            method="POST",
            path="/search/name",
            visible_fields=["name", "domain"],
            body_builder=lambda v: {
                "name": getattr(v, "name", None) or "",
                "domain": getattr(v, "domain", None) or "",
            },
        ),
        OpSpec(
            id="find_email_from_linkedin",
            label="Find Email from LinkedIn URL",
            method="POST",
            path="/search/linkedin",
            visible_fields=["linkedin_url"],
            body_builder=lambda v: {"linkedin_url": getattr(v, "linkedin_url", None) or ""},
        ),
        OpSpec(
            id="verify_email",
            label="Verify Email",
            method="POST",
            path="/verify",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", None) or ""},
        ),
        OpSpec(
            id="reverse_email_lookup",
            label="Reverse Email Lookup",
            method="POST",
            path="/reverse",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", None) or ""},
        ),
        OpSpec(
            id="get_credits",
            label="Get Remaining Credits",
            method="GET",
            path="/credits",
        ),
    ],
    outputs_schema=[
        {"label": "email", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "domain", "type": "string"},
        {"label": "linkedin_url", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "credits", "type": "number"},
    ],
    allow_error=True,
)
