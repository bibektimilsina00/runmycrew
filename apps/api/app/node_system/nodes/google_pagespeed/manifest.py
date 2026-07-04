"""Google PageSpeed Insights action node — PageSpeed Insights — Lighthouse audits for a URL.

REST at https://www.googleapis.com/pagespeedonline/v5. See sim-parity roadmap Phase 4.27.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_pagespeed",
    name="Google PageSpeed Insights",
    category="integration",
    description="PageSpeed Insights — Lighthouse audits for a URL.",
    icon_slug="google_pagespeed",
    color="#4285F4",
    base_url="https://www.googleapis.com/pagespeedonline/v5",
    credential_type="google_pagespeed_api_key",
    token_field=["api_key"],
    auth="query_token",
    auth_query_param="key",
    fields=[
        FieldSpec(name="url", label="URL", type="string"),
        FieldSpec(name="strategy", label="Strategy", type="string", default="mobile"),
        FieldSpec(name="category", label="Category", type="string", default="performance"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(
            name="max_results", label="Max Results", type="number", default=10, mode="advanced"
        ),
        FieldSpec(name="volume_id", label="Volume ID", type="string"),
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="customer", label="Customer", type="string", default="my_customer"),
        FieldSpec(name="group_key", label="Group Key", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="role", label="Role", type="string", default="MEMBER"),
        FieldSpec(name="member_key", label="Member Key", type="string"),
    ],
    operations=[
        OpSpec(
            id="run_audit",
            label="Run Audit",
            method="GET",
            path="/runPagespeed",
            visible_fields=["url", "strategy", "category"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "url": getattr(v, "url", "") or "",
                    "strategy": getattr(v, "strategy", None) or None,
                    "category": getattr(v, "category", None) or None,
                }.items()
                if val
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
