"""Dropcontact action node — email finder + enrichment.

REST at https://api.dropcontact.com. Header auth via X-Access-Token.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.dropcontact",
    name="Dropcontact",
    category="integration",
    description="Dropcontact — GDPR-friendly B2B email enrichment.",
    icon_slug="dropcontact",
    color="#1c1c1c",
    base_url="https://api.dropcontact.com",
    credential_type="dropcontact_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-Access-Token",
    fields=[
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="company", label="Company", type="string"),
        FieldSpec(name="website", label="Website", type="string"),
        FieldSpec(name="linkedin", label="LinkedIn URL", type="string"),
        FieldSpec(name="request_id", label="Request ID (for status check)", type="string"),
        FieldSpec(
            name="siren",
            label="Siren source (data country)",
            type="string",
            default="false",
            mode="advanced",
        ),
        FieldSpec(name="language", label="Language", type="string", default="en", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="enrich_batch",
            label="Enrich Batch (submit)",
            method="POST",
            path="/batch",
            visible_fields=[
                "first_name",
                "last_name",
                "email",
                "company",
                "website",
                "linkedin",
                "language",
                "siren",
            ],
            body_builder=lambda v: {
                "data": [
                    {
                        k: val
                        for k, val in {
                            "first_name": getattr(v, "first_name", None) or None,
                            "last_name": getattr(v, "last_name", None) or None,
                            "email": getattr(v, "email", None) or None,
                            "company": getattr(v, "company", None) or None,
                            "website": getattr(v, "website", None) or None,
                            "linkedin": getattr(v, "linkedin", None) or None,
                        }.items()
                        if val is not None
                    }
                ],
                "siren": (getattr(v, "siren", None) or "false").lower() == "true",
                "language": getattr(v, "language", None) or "en",
            },
        ),
        OpSpec(
            id="fetch_batch_result",
            label="Fetch Batch Result",
            method="GET",
            path="/batch/{request_id}",
            visible_fields=["request_id"],
        ),
    ],
    outputs_schema=[
        {"label": "request_id", "type": "string"},
        {"label": "data", "type": "array"},
        {"label": "success", "type": "boolean"},
    ],
    allow_error=True,
)
