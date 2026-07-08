"""Brandfetch action node — manifest form.

Brandfetch resolves brand assets (logos, colors, fonts, social links)
from a domain or a free-text query. Both ops are GETs with the lookup
key in the path — no query/body fields needed.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.brandfetch",
    name="Brandfetch",
    category="integration",
    description="Pull brand identity (logos, colors, fonts, links) by domain or query.",
    icon_slug="brandfetch",
    color="#ffffff",
    base_url="https://api.brandfetch.io/v2",
    credential_type="brandfetch_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="domain",
            label="Domain",
            type="string",
            placeholder="airbnb.com",
        ),
        FieldSpec(
            name="query",
            label="Query",
            type="string",
            placeholder="airbnb",
        ),
    ],
    operations=[
        OpSpec(
            id="get_brand",
            label="Get Brand by Domain",
            method="GET",
            path="/brands/{domain}",
            visible_fields=["domain"],
        ),
        OpSpec(
            id="search",
            label="Search Brands",
            method="GET",
            path="/search/{query}",
            visible_fields=["query"],
        ),
    ],
    outputs_schema=[
        {"label": "name", "type": "string"},
        {"label": "domain", "type": "string"},
        {"label": "logos", "type": "array"},
        {"label": "colors", "type": "array"},
        {"label": "fonts", "type": "array"},
        {"label": "links", "type": "array"},
        {"label": "description", "type": "string"},
    ],
    allow_error=True,
)
