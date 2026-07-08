"""Exa action node — manifest form.

Exa.ai serves neural + keyword web search with content extraction. Auth
uses a custom `x-api-key` header (lowercased), not Bearer, so the
manifest uses `header_token` with `auth_header_name="x-api-key"`.

Three ops the workflows care about: semantic search, find-similar
(give a URL, get neighbors in embedding space), and contents (full
text extraction by URL list).
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    register_flatten,
)


def _flatten_results(body: Any) -> dict[str, Any]:
    """Exa wraps results in `{results: [...], requestId, ...}` — surface
    the list directly + the count for downstream nodes."""
    if not isinstance(body, dict):
        return {}
    results = body.get("results") or []
    return {
        "results": results,
        "count": len(results) if isinstance(results, list) else 0,
        "request_id": body.get("requestId"),
    }


register_flatten("exa.results", _flatten_results)

MANIFEST = ProviderManifest(
    type="action.exa",
    name="Exa",
    category="integration",
    description="Neural web search, find-similar pages, and full-text content extraction.",
    icon_slug="exa",
    color="#ffffff",
    base_url="https://api.exa.ai",
    credential_type="exa_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="x-api-key",
    fields=[
        FieldSpec(name="query", label="Query", type="string", placeholder="latest LLM papers"),
        FieldSpec(name="url", label="URL", type="string", placeholder="https://example.com"),
        FieldSpec(name="urls", label="URLs (JSON array)", type="json"),
        FieldSpec(name="num_results", label="Results", type="number", default=10, mode="advanced"),
        FieldSpec(
            name="category",
            label="Category",
            type="options",
            mode="advanced",
            options=[
                {"label": "(any)", "value": ""},
                {"label": "Company", "value": "company"},
                {"label": "Research paper", "value": "research paper"},
                {"label": "News", "value": "news"},
                {"label": "GitHub", "value": "github"},
                {"label": "Tweet", "value": "tweet"},
                {"label": "PDF", "value": "pdf"},
            ],
        ),
    ],
    operations=[
        OpSpec(
            id="search",
            label="Search",
            method="POST",
            path="/search",
            visible_fields=["query", "num_results", "category"],
            body_fields=["query", "category"],
            body_template={"numResults": "{num_results}"},
            output_flatten="exa.results",
        ),
        OpSpec(
            id="find_similar",
            label="Find Similar",
            method="POST",
            path="/findSimilar",
            visible_fields=["url", "num_results"],
            body_fields=["url"],
            body_template={"numResults": "{num_results}"},
            output_flatten="exa.results",
        ),
        OpSpec(
            id="contents",
            label="Get Contents",
            method="POST",
            path="/contents",
            visible_fields=["urls"],
            body_fields=["urls"],
            output_flatten="exa.results",
        ),
    ],
    outputs_schema=[
        {"label": "results", "type": "array"},
        {"label": "count", "type": "number"},
        {"label": "request_id", "type": "string"},
    ],
    allow_error=True,
)
