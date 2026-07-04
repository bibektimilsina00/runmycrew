"""Ahrefs action node — Ahrefs — SEO + backlinks + keyword research.

REST at https://apiv2.ahrefs.com. See sim-parity roadmap Phase 4.16/4.17.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.ahrefs",
    name="Ahrefs",
    category="integration",
    description="Ahrefs — SEO + backlinks + keyword research.",
    icon_slug="ahrefs",
    color="#1c1c1c",
    base_url="https://apiv2.ahrefs.com",
    credential_type="ahrefs_api_key",
    token_field=["api_key"],
    auth="bearer",
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
            id="domain_overview",
            label="Domain Overview",
            method="GET",
            path="/",
            visible_fields=["domain"],
            query_builder=lambda v: {
                "target": getattr(v, "domain", "") or "",
                "output": "json",
                "mode": "domain",
                "from": "domain_rating",
            },
        ),
        OpSpec(
            id="backlinks",
            label="Backlinks",
            method="GET",
            path="/",
            visible_fields=["domain", "limit"],
            query_builder=lambda v: {
                "target": getattr(v, "domain", "") or "",
                "output": "json",
                "mode": "domain",
                "from": "backlinks",
                "limit": int(getattr(v, "limit", 100) or 100),
            },
        ),
        OpSpec(
            id="referring_domains",
            label="Referring Domains",
            method="GET",
            path="/",
            visible_fields=["domain", "limit"],
            query_builder=lambda v: {
                "target": getattr(v, "domain", "") or "",
                "output": "json",
                "mode": "domain",
                "from": "refdomains",
                "limit": int(getattr(v, "limit", 100) or 100),
            },
        ),
        OpSpec(
            id="organic_keywords",
            label="Organic Keywords",
            method="GET",
            path="/",
            visible_fields=["domain", "limit"],
            query_builder=lambda v: {
                "target": getattr(v, "domain", "") or "",
                "output": "json",
                "mode": "domain",
                "from": "positions",
                "limit": int(getattr(v, "limit", 100) or 100),
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
