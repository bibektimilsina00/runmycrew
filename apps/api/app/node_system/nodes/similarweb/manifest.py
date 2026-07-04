"""SimilarWeb action node — SimilarWeb — website + market intelligence.

REST at https://api.similarweb.com/v1. See sim-parity roadmap Phase 4.16/4.17.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.similarweb",
    name="SimilarWeb",
    category="integration",
    description="SimilarWeb — website + market intelligence.",
    icon_slug="similarweb",
    color="#1c1c1c",
    base_url="https://api.similarweb.com/v1",
    credential_type="similarweb_api_key",
    token_field=["api_key"],
    auth="query_token",
    auth_query_param="api_key",
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
            id="website_total_traffic",
            label="Website Total Traffic",
            method="GET",
            path="/website/{domain}/total-traffic-and-engagement/visits",
            visible_fields=["domain", "start_date", "end_date"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "start_date": getattr(v, "start_date", None) or None,
                    "end_date": getattr(v, "end_date", None) or None,
                    "country": "world",
                    "granularity": "monthly",
                    "main_domain_only": "false",
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="website_traffic_sources",
            label="Traffic Sources",
            method="GET",
            path="/website/{domain}/traffic-sources/overview-share",
            visible_fields=["domain", "start_date", "end_date"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "start_date": getattr(v, "start_date", None) or None,
                    "end_date": getattr(v, "end_date", None) or None,
                    "country": "world",
                    "granularity": "monthly",
                    "main_domain_only": "false",
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="website_geography",
            label="Geographic Distribution",
            method="GET",
            path="/website/{domain}/geo/traffic-by-country",
            visible_fields=["domain", "start_date", "end_date"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "start_date": getattr(v, "start_date", None) or None,
                    "end_date": getattr(v, "end_date", None) or None,
                    "granularity": "monthly",
                    "main_domain_only": "false",
                }.items()
                if val is not None
            },
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
