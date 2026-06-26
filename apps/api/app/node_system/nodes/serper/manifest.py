"""Serper action node — manifest form.

Serper.dev is a Google-SERP wrapper — same query shape across the
four endpoints we expose (`/search`, `/images`, `/news`, `/places`).
Auth is the custom `X-API-KEY` header.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.serper",
    name="Serper",
    category="integration",
    description="Google search results (web, images, news, places) via Serper.dev.",
    icon_slug="serper",
    color="#1c1c1c",
    base_url="https://google.serper.dev",
    credential_type="serper_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-API-KEY",
    fields=[
        FieldSpec(
            name="q", label="Query", type="string", required=True, placeholder="search query"
        ),
        FieldSpec(
            name="gl",
            label="Country",
            type="string",
            default="us",
            mode="advanced",
            placeholder="us | uk | in | …",
        ),
        FieldSpec(
            name="hl",
            label="Language",
            type="string",
            default="en",
            mode="advanced",
            placeholder="en | es | de | …",
        ),
        FieldSpec(name="num", label="Results", type="number", default=10, mode="advanced"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="search",
            label="Web Search",
            method="POST",
            path="/search",
            visible_fields=["q", "gl", "hl", "num", "page"],
            body_fields=["q", "gl", "hl", "num", "page"],
        ),
        OpSpec(
            id="images",
            label="Image Search",
            method="POST",
            path="/images",
            visible_fields=["q", "gl", "hl", "num", "page"],
            body_fields=["q", "gl", "hl", "num", "page"],
        ),
        OpSpec(
            id="news",
            label="News Search",
            method="POST",
            path="/news",
            visible_fields=["q", "gl", "hl", "num", "page"],
            body_fields=["q", "gl", "hl", "num", "page"],
        ),
        OpSpec(
            id="places",
            label="Places Search",
            method="POST",
            path="/places",
            visible_fields=["q", "gl", "hl", "num", "page"],
            body_fields=["q", "gl", "hl", "num", "page"],
        ),
    ],
    outputs_schema=[
        {"label": "organic", "type": "array"},
        {"label": "images", "type": "array"},
        {"label": "news", "type": "array"},
        {"label": "places", "type": "array"},
        {"label": "knowledgeGraph", "type": "object"},
        {"label": "searchParameters", "type": "object"},
    ],
    allow_error=True,
)
