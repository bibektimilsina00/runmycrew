"""Firecrawl action node — manifest form.

Pure-declarative REST. Firecrawl's API has a uniform shape across the
four ops we expose (scrape / crawl / map / search): each is a single
POST that takes a JSON body and returns either a `{success, data}`
wrapper (scrape, map, search) or a `{id, url}` job handle (crawl —
asynchronous, callers poll status separately).

Validates the `/new-integration` skill end-to-end — every escape
hatch stays dormant; everything below is plain manifest data.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    register_flatten,
)


def _unwrap_data(body: Any) -> Any:
    """Firecrawl wraps successful responses in `{success: true, data: ...}`.
    Strip the envelope so downstream nodes see the raw payload."""
    if not isinstance(body, dict):
        return body
    if body.get("success") is True and "data" in body:
        return body["data"]
    return body


register_flatten("firecrawl.data", _unwrap_data)


MANIFEST = ProviderManifest(
    type="action.firecrawl",
    name="Firecrawl",
    category="integration",
    description="Scrape, crawl, map, and search the web — Firecrawl turns "
    "any site into LLM-ready markdown.",
    icon_slug="firecrawl",
    color="#1c1c1c",
    base_url="https://api.firecrawl.dev/v1",
    credential_type="firecrawl_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="url",
            label="URL",
            type="string",
            required=True,
            placeholder="https://example.com",
        ),
        FieldSpec(
            name="query",
            label="Query",
            type="string",
            placeholder="latest LLM papers",
        ),
        FieldSpec(
            name="limit",
            label="Limit",
            type="number",
            default=10,
            mode="advanced",
        ),
        FieldSpec(
            name="formats",
            label="Formats (JSON array)",
            type="json",
            placeholder='["markdown", "html"]',
            mode="advanced",
            description='List of output formats. Defaults to ["markdown"].',
        ),
    ],
    operations=[
        OpSpec(
            id="scrape",
            label="Scrape",
            method="POST",
            path="/scrape",
            visible_fields=["url", "formats"],
            body_fields=["url", "formats"],
            output_flatten="firecrawl.data",
        ),
        OpSpec(
            id="crawl",
            label="Crawl",
            method="POST",
            path="/crawl",
            visible_fields=["url", "limit", "formats"],
            body_fields=["url", "limit", "formats"],
        ),
        OpSpec(
            id="map",
            label="Map",
            method="POST",
            path="/map",
            visible_fields=["url"],
            body_fields=["url"],
            output_flatten="firecrawl.data",
        ),
        OpSpec(
            id="search",
            label="Search",
            method="POST",
            path="/search",
            visible_fields=["query", "limit"],
            body_fields=["query", "limit"],
            output_flatten="firecrawl.data",
        ),
    ],
    outputs_schema=[
        {"label": "markdown", "type": "string"},
        {"label": "html", "type": "string"},
        {"label": "metadata", "type": "object"},
        {"label": "links", "type": "array"},
        {"label": "id", "type": "string"},
        {"label": "url", "type": "string"},
    ],
    allow_error=True,
)
