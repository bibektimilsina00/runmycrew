"""Wiza action node — Wiza — LinkedIn scraper + email enrichment.

REST at https://wiza.co/api. See sim-parity roadmap Phase 4.16/4.17.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.wiza",
    name="Wiza",
    category="integration",
    description="Wiza — LinkedIn scraper + email enrichment.",
    icon_slug="wiza",
    color="#1c1c1c",
    base_url="https://wiza.co/api",
    credential_type="wiza_api_key",
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
            id="prospect_search",
            label="Prospect Search (LinkedIn URL)",
            method="POST",
            path="/prospects/reveal",
            visible_fields=["linkedin_url"],
            body_builder=lambda v: {"linkedin_url": getattr(v, "linkedin_url", "") or ""},
        ),
        OpSpec(
            id="list_lists",
            label="List All Lists",
            method="GET",
            path="/lists",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_list",
            label="Get List",
            method="GET",
            path="/lists/{list_id}",
            visible_fields=["list_id"],
            query_builder=lambda v: {},
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
