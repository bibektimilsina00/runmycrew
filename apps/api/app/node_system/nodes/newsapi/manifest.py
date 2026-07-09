"""NewsAPI action node — manifest form.

newsapi.org aggregates 80k+ news sources. ApiKey via the
`X-Api-Key` header. Three ops:

  - everything — full-text search across articles.
  - top_headlines — top stories per country / category / source.
  - sources — list of supported publishers.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

_COMMON_FIELDS = ["q", "language", "page_size", "page"]

MANIFEST = ProviderManifest(
    type="action.newsapi",
    name="NewsAPI",
    category="integration",
    description="Search 80k+ news sources via newsapi.org — articles, headlines, sources.",
    icon_slug="newsapi",
    color="#ffffff",
    base_url="https://newsapi.org/v2",
    credential_type="newsapi_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-Api-Key",
    fields=[
        FieldSpec(name="q", label="Query", type="string", placeholder="apple stock"),
        FieldSpec(
            name="language",
            label="Language",
            type="string",
            default="en",
            mode="advanced",
            placeholder="en | es | de | …",
        ),
        FieldSpec(name="page_size", label="Page size", type="number", default=20, mode="advanced"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
        FieldSpec(
            name="country", label="Country", type="string", placeholder="us", mode="advanced"
        ),
        FieldSpec(
            name="category",
            label="Category",
            type="options",
            mode="advanced",
            options=[
                {"label": "(any)", "value": ""},
                {"label": "business", "value": "business"},
                {"label": "entertainment", "value": "entertainment"},
                {"label": "general", "value": "general"},
                {"label": "health", "value": "health"},
                {"label": "science", "value": "science"},
                {"label": "sports", "value": "sports"},
                {"label": "technology", "value": "technology"},
            ],
        ),
        FieldSpec(
            name="sources",
            label="Sources (CSV)",
            type="string",
            remote=RemoteLookup(provider="newsapi", resource="sources"),
        ),
        FieldSpec(name="from_date", label="From (YYYY-MM-DD)", type="string", mode="advanced"),
        FieldSpec(name="to_date", label="To (YYYY-MM-DD)", type="string", mode="advanced"),
        FieldSpec(
            name="sort_by",
            label="Sort By",
            type="options",
            mode="advanced",
            options=[
                {"label": "relevancy", "value": "relevancy"},
                {"label": "popularity", "value": "popularity"},
                {"label": "publishedAt", "value": "publishedAt"},
            ],
        ),
    ],
    operations=[
        OpSpec(
            id="everything",
            label="Search Everything",
            method="GET",
            path="/everything",
            visible_fields=_COMMON_FIELDS + ["sources", "from_date", "to_date", "sort_by"],
            query_builder=lambda props: {
                k: v
                for k, v in {
                    "q": getattr(props, "q", None),
                    "language": getattr(props, "language", None),
                    "pageSize": getattr(props, "page_size", None),
                    "page": getattr(props, "page", None),
                    "sources": getattr(props, "sources", None),
                    "from": getattr(props, "from_date", None),
                    "to": getattr(props, "to_date", None),
                    "sortBy": getattr(props, "sort_by", None),
                }.items()
                if v not in (None, "")
            },
        ),
        OpSpec(
            id="top_headlines",
            label="Top Headlines",
            method="GET",
            path="/top-headlines",
            visible_fields=_COMMON_FIELDS + ["country", "category", "sources"],
            query_builder=lambda props: {
                k: v
                for k, v in {
                    "q": getattr(props, "q", None),
                    "language": getattr(props, "language", None),
                    "pageSize": getattr(props, "page_size", None),
                    "page": getattr(props, "page", None),
                    "country": getattr(props, "country", None),
                    "category": getattr(props, "category", None),
                    "sources": getattr(props, "sources", None),
                }.items()
                if v not in (None, "")
            },
        ),
        OpSpec(
            id="sources",
            label="List Sources",
            method="GET",
            path="/top-headlines/sources",
            visible_fields=["category", "language", "country"],
            query_builder=lambda props: {
                k: v
                for k, v in {
                    "category": getattr(props, "category", None),
                    "language": getattr(props, "language", None),
                    "country": getattr(props, "country", None),
                }.items()
                if v not in (None, "")
            },
        ),
    ],
    outputs_schema=[
        {"label": "status", "type": "string"},
        {"label": "totalResults", "type": "number"},
        {"label": "articles", "type": "array"},
        {"label": "sources", "type": "array"},
    ],
    allow_error=True,
)
