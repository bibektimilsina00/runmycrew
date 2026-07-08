"""Google Books action node — Google Books — search + fetch volume metadata.

REST at https://www.googleapis.com/books/v1. See sim-parity roadmap Phase 4.27.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_books",
    name="Google Books",
    category="integration",
    description="Google Books — search + fetch volume metadata.",
    icon_slug="google_books",
    color="#ffffff",
    base_url="https://www.googleapis.com/books/v1",
    credential_type="google_books_api_key",
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
            id="search_volumes",
            label="Search Volumes",
            method="GET",
            path="/volumes",
            visible_fields=["query", "max_results"],
            query_builder=lambda v: {
                "q": getattr(v, "query", "") or "",
                "maxResults": int(getattr(v, "max_results", 10) or 10),
            },
        ),
        OpSpec(
            id="get_volume",
            label="Get Volume",
            method="GET",
            path="/volumes/{volume_id}",
            visible_fields=["volume_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
