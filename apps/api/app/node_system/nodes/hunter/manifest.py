"""Hunter.io action node — email finder + verifier.

REST at https://api.hunter.io/v2. API key rides as ?api_key= query param
(query_token scheme).
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.hunter",
    name="Hunter.io",
    category="integration",
    description="Hunter — find + verify emails by domain, name, or company.",
    icon_slug="hunter",
    color="#1c1c1c",
    base_url="https://api.hunter.io/v2",
    credential_type="hunter_api_key",
    token_field=["api_key"],
    auth="query_token",
    auth_query_param="api_key",
    fields=[
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="email", label="Email (for verify / lookup)", type="string"),
        FieldSpec(name="company", label="Company Name", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=10, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="domain_search",
            label="Domain Search",
            method="GET",
            path="/domain-search",
            visible_fields=["domain", "company", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "domain": getattr(v, "domain", None) or None,
                    "company": getattr(v, "company", None) or None,
                    "limit": int(getattr(v, "limit", 10) or 10),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="email_finder",
            label="Email Finder",
            method="GET",
            path="/email-finder",
            visible_fields=["domain", "first_name", "last_name", "company"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "domain": getattr(v, "domain", None) or None,
                    "company": getattr(v, "company", None) or None,
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="email_verifier",
            label="Verify Email",
            method="GET",
            path="/email-verifier",
            visible_fields=["email"],
            query_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        OpSpec(
            id="email_count",
            label="Count Emails on Domain",
            method="GET",
            path="/email-count",
            visible_fields=["domain", "company"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "domain": getattr(v, "domain", None) or None,
                    "company": getattr(v, "company", None) or None,
                }.items()
                if val is not None
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "emails", "type": "array"},
        {"label": "email", "type": "string"},
        {"label": "score", "type": "number"},
        {"label": "result", "type": "string"},
    ],
    allow_error=True,
)
