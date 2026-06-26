"""Wikipedia action node — manifest form.

Wikipedia's REST v1 API serves clean JSON (no auth required, no
credentials, just a polite User-Agent). Three ops cover the high-value
calls: page summary (LLM-grounding cards), full HTML, and search.

Search lives on the older MediaWiki action API (`/w/api.php`) at a
different path than the REST endpoints — we keep both under one
manifest with `base_url` set to the wiki host and op paths spelling
out the rest.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.wikipedia",
    name="Wikipedia",
    category="integration",
    description="Wikipedia page summary, full HTML, and search — no API key required.",
    icon_slug="wikipedia",
    color="#ffffff",
    base_url="https://en.wikipedia.org",
    credential_type=None,
    auth="none",
    extra_headers={"User-Agent": "RunMyCrew/1.0 (workflow automation)"},
    fields=[
        FieldSpec(name="title", label="Page Title", type="string", placeholder="Albert Einstein"),
        FieldSpec(name="query", label="Search Query", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=10, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="summary",
            label="Page Summary",
            method="GET",
            path="/api/rest_v1/page/summary/{title}",
            visible_fields=["title"],
        ),
        OpSpec(
            id="html",
            label="Page HTML",
            method="GET",
            path="/api/rest_v1/page/html/{title}",
            visible_fields=["title"],
        ),
        OpSpec(
            id="search",
            label="Search",
            method="GET",
            path="/w/api.php",
            visible_fields=["query", "limit"],
            query_builder=lambda props: {
                "action": "query",
                "list": "search",
                "format": "json",
                "srsearch": getattr(props, "query", None) or "",
                "srlimit": int(getattr(props, "limit", None) or 10),
            },
        ),
    ],
    outputs_schema=[
        {"label": "title", "type": "string"},
        {"label": "extract", "type": "string"},
        {"label": "description", "type": "string"},
        {"label": "thumbnail", "type": "object"},
        {"label": "content_urls", "type": "object"},
        {"label": "query", "type": "object"},
    ],
    allow_error=True,
)
