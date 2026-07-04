"""LeadMagic action node — LeadMagic — email finder + waterfall enrichment.

REST at https://api.leadmagic.io. See sim-parity roadmap §4.15.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.leadmagic",
    name="LeadMagic",
    category="integration",
    description="LeadMagic — email finder + waterfall enrichment.",
    icon_slug="leadmagic",
    color="#1c1c1c",
    base_url="https://api.leadmagic.io",
    credential_type="leadmagic_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-API-Key",
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
        OpSpec(
            id="validate_email",
            label="Validate Email",
            method="POST",
            path="/email-validate",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        OpSpec(
            id="enrich_person",
            label="Enrich Person",
            method="POST",
            path="/personal-email-finder",
            visible_fields=["linkedin_url"],
            body_builder=lambda v: {"profile_url": getattr(v, "linkedin_url", "") or ""},
        ),
        OpSpec(
            id="company_search",
            label="Company Search",
            method="POST",
            path="/company-search",
            visible_fields=["company", "domain"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "company_name": getattr(v, "company", None) or None,
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
