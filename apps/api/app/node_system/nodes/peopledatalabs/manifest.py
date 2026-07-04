"""People Data Labs action node — person + company enrichment.

REST at https://api.peopledatalabs.com/v5. API key as X-Api-Key header.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.peopledatalabs",
    name="People Data Labs",
    category="integration",
    description="People Data Labs — person + company enrichment API.",
    icon_slug="peopledatalabs",
    color="#1c1c1c",
    base_url="https://api.peopledatalabs.com/v5",
    credential_type="peopledatalabs_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-Api-Key",
    fields=[
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="phone", label="Phone", type="string"),
        FieldSpec(name="linkedin", label="LinkedIn URL", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="company", label="Company", type="string"),
        FieldSpec(name="website", label="Company Website / Domain", type="string"),
        FieldSpec(name="ticker", label="Ticker", type="string"),
        FieldSpec(name="query", label="Elasticsearch DSL (advanced)", type="json", mode="advanced"),
        FieldSpec(name="size", label="Size", type="number", default=10, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="person_enrichment",
            label="Person Enrichment",
            method="GET",
            path="/person/enrich",
            visible_fields=["email", "phone", "linkedin", "first_name", "last_name", "company"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None) or None,
                    "phone": getattr(v, "phone", None) or None,
                    "profile": getattr(v, "linkedin", None) or None,
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                    "company": getattr(v, "company", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="person_search",
            label="Person Search",
            method="POST",
            path="/person/search",
            visible_fields=["query", "size"],
            body_builder=lambda v: {
                "query": getattr(v, "query", None) or {},
                "size": int(getattr(v, "size", 10) or 10),
            },
        ),
        OpSpec(
            id="company_enrichment",
            label="Company Enrichment",
            method="GET",
            path="/company/enrich",
            visible_fields=["website", "company", "ticker"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "website": getattr(v, "website", None) or None,
                    "name": getattr(v, "company", None) or None,
                    "ticker": getattr(v, "ticker", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="company_search",
            label="Company Search",
            method="POST",
            path="/company/search",
            visible_fields=["query", "size"],
            body_builder=lambda v: {
                "query": getattr(v, "query", None) or {},
                "size": int(getattr(v, "size", 10) or 10),
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "status", "type": "number"},
        {"label": "likelihood", "type": "number"},
    ],
    allow_error=True,
)
