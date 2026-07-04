"""Tavily action node — manifest form.

Tavily is an AI-native search API tuned for LLM grounding. Two ops:

  - `search` — natural-language query → ranked passages + answer.
  - `extract` — given a URL list, pull clean text contents.

Auth is bearer-token; nothing unusual. Pure declarative manifest.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    register_flatten,
)


def _flatten_search(body: Any) -> dict[str, Any]:
    """Tavily `/search` response: `{answer, results, ...}`. Pass through
    the high-value keys so workflows don't have to dig."""
    if not isinstance(body, dict):
        return {}
    return {
        "answer": body.get("answer"),
        "query": body.get("query"),
        "results": body.get("results") or [],
        "images": body.get("images") or [],
        "follow_up_questions": body.get("follow_up_questions") or [],
    }


def _flatten_extract(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {}
    return {
        "results": body.get("results") or [],
        "failed_results": body.get("failed_results") or [],
        "response_time": body.get("response_time"),
    }


register_flatten("tavily.search", _flatten_search)
register_flatten("tavily.extract", _flatten_extract)


MANIFEST = ProviderManifest(
    type="action.tavily",
    name="Tavily",
    category="integration",
    description="LLM-grounded web search + URL extraction tuned for RAG and agents.",
    icon_slug="tavily",
    color="#1c1c1c",
    base_url="https://api.tavily.com",
    credential_type="tavily_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="query", label="Query", type="string", placeholder="search query"),
        FieldSpec(name="urls", label="URLs (JSON array)", type="json"),
        FieldSpec(
            name="search_depth",
            label="Search Depth",
            type="options",
            default="basic",
            mode="advanced",
            options=[
                {"label": "Basic", "value": "basic"},
                {"label": "Advanced", "value": "advanced"},
            ],
        ),
        FieldSpec(
            name="topic",
            label="Topic",
            type="options",
            default="general",
            mode="advanced",
            options=[
                {"label": "General", "value": "general"},
                {"label": "News", "value": "news"},
                {"label": "Finance", "value": "finance"},
            ],
        ),
        FieldSpec(
            name="max_results",
            label="Max Results",
            type="number",
            default=5,
            mode="advanced",
        ),
        FieldSpec(
            name="include_answer",
            label="Include Answer",
            type="boolean",
            default=True,
            mode="advanced",
        ),
        FieldSpec(
            name="include_images",
            label="Include Images",
            type="boolean",
            default=False,
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="search",
            label="Search",
            method="POST",
            path="/search",
            visible_fields=[
                "query",
                "search_depth",
                "topic",
                "max_results",
                "include_answer",
                "include_images",
            ],
            body_fields=[
                "query",
                "search_depth",
                "topic",
                "max_results",
                "include_answer",
                "include_images",
            ],
            output_flatten="tavily.search",
        ),
        OpSpec(
            id="extract",
            label="Extract URLs",
            method="POST",
            path="/extract",
            visible_fields=["urls"],
            body_fields=["urls"],
            output_flatten="tavily.extract",
        ),
    ],
    outputs_schema=[
        {"label": "answer", "type": "string"},
        {"label": "results", "type": "array"},
        {"label": "images", "type": "array"},
        {"label": "follow_up_questions", "type": "array"},
        {"label": "failed_results", "type": "array"},
    ],
    allow_error=True,
)
