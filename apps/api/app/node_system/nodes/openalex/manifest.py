"""OpenAlex action node — manifest form.

OpenAlex serves an open scholarly graph (works / authors / venues /
concepts / institutions). No auth required; the project asks you to
pass an email in `User-Agent` or `mailto=` for the polite pool. We set
a default polite header and let users override per workspace later.

Five ops — one list per entity. All identical shape: a `search` query
+ filters + pagination, returning `{results, meta, group_by}`.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_COMMON_QUERY_FIELDS = ["search", "filter", "per_page", "page", "sort"]
_COMMON_VISIBLE = _COMMON_QUERY_FIELDS


MANIFEST = ProviderManifest(
    type="action.openalex",
    name="OpenAlex",
    category="integration",
    description="Open scholarly graph — search works, authors, venues, and concepts.",
    icon_slug="openalex",
    color="#1c1c1c",
    base_url="https://api.openalex.org",
    credential_type=None,
    auth="none",
    extra_headers={"User-Agent": "RunMyCrew/1.0 (mailto:noreply@runmycrew.com)"},
    fields=[
        FieldSpec(name="search", label="Search", type="string", placeholder="machine learning"),
        FieldSpec(
            name="filter",
            label="Filter",
            type="string",
            placeholder="publication_year:2024",
            mode="advanced",
            description="OpenAlex filter syntax (key:value, comma-joined).",
        ),
        FieldSpec(name="per_page", label="Per page", type="number", default=25, mode="advanced"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
        FieldSpec(name="sort", label="Sort", type="string", mode="advanced"),
        FieldSpec(name="entity_id", label="Entity ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="search_works",
            label="Search Works",
            method="GET",
            path="/works",
            visible_fields=_COMMON_VISIBLE,
            query_fields=_COMMON_QUERY_FIELDS,
        ),
        OpSpec(
            id="search_authors",
            label="Search Authors",
            method="GET",
            path="/authors",
            visible_fields=_COMMON_VISIBLE,
            query_fields=_COMMON_QUERY_FIELDS,
        ),
        OpSpec(
            id="search_venues",
            label="Search Venues",
            method="GET",
            path="/sources",
            visible_fields=_COMMON_VISIBLE,
            query_fields=_COMMON_QUERY_FIELDS,
        ),
        OpSpec(
            id="search_concepts",
            label="Search Concepts",
            method="GET",
            path="/concepts",
            visible_fields=_COMMON_VISIBLE,
            query_fields=_COMMON_QUERY_FIELDS,
        ),
        OpSpec(
            id="get_work",
            label="Get Work by ID",
            method="GET",
            path="/works/{entity_id}",
            visible_fields=["entity_id"],
        ),
    ],
    outputs_schema=[
        {"label": "results", "type": "array"},
        {"label": "meta", "type": "object"},
        {"label": "group_by", "type": "array"},
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
    ],
    allow_error=True,
)
