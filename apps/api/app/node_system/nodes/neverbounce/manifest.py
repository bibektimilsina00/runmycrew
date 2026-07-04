"""NeverBounce action node — NeverBounce — real-time email verification.

REST at https://api.neverbounce.com/v4. See sim-parity roadmap Phase 4.16/4.17.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.neverbounce",
    name="NeverBounce",
    category="integration",
    description="NeverBounce — real-time email verification.",
    icon_slug="neverbounce",
    color="#1c1c1c",
    base_url="https://api.neverbounce.com/v4",
    credential_type="neverbounce_api_key",
    token_field=["api_key"],
    auth="query_token",
    auth_query_param="key",
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
            id="single_check",
            label="Verify Email",
            method="GET",
            path="/single/check",
            visible_fields=["email"],
            query_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        OpSpec(
            id="get_credits",
            label="Get Credits",
            method="GET",
            path="/account/info",
            visible_fields=[],
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
