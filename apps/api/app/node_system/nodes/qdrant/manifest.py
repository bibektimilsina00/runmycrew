"""Qdrant action node — manifest form.

Qdrant clusters live at per-deployment URLs (cloud:
`https://abc.us-east-1-0.aws.cloud.qdrant.io:6333`; self-host: any
URL the user provides). Credential carries `cluster_url` + `api_key`.
Auth uses Qdrant's `api-key` header.

Six ops cover the routine workflow needs: list/create/delete
collections, upsert/search/delete points.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.qdrant",
    name="Qdrant",
    category="integration",
    description="Qdrant vector database — manage collections + upsert/search points.",
    icon_slug="qdrant",
    color="#1c1c1c",
    base_url="",
    credential_type="qdrant_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="api-key",
    fields=[
        FieldSpec(name="collection", label="Collection Name", type="string"),
        FieldSpec(name="size", label="Vector Size", type="number", mode="advanced"),
        FieldSpec(
            name="distance",
            label="Distance",
            type="options",
            default="Cosine",
            mode="advanced",
            options=[
                {"label": "Cosine", "value": "Cosine"},
                {"label": "Euclid", "value": "Euclid"},
                {"label": "Dot", "value": "Dot"},
                {"label": "Manhattan", "value": "Manhattan"},
            ],
        ),
        FieldSpec(name="points", label="Points (JSON array)", type="json"),
        FieldSpec(name="vector", label="Query Vector (JSON array)", type="json"),
        FieldSpec(name="ids", label="Point IDs (JSON array)", type="json"),
        FieldSpec(name="limit", label="Limit", type="number", default=10, mode="advanced"),
        FieldSpec(name="filter", label="Filter (JSON)", type="json", mode="advanced"),
        FieldSpec(
            name="with_payload",
            label="Include payload",
            type="boolean",
            default=True,
            mode="advanced",
        ),
        FieldSpec(
            name="with_vector",
            label="Include vector",
            type="boolean",
            default=False,
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="list_collections",
            label="List Collections",
            method="GET",
            path="{cluster_url}/collections",
        ),
        OpSpec(
            id="get_collection",
            label="Get Collection",
            method="GET",
            path="{cluster_url}/collections/{collection}",
            visible_fields=["collection"],
        ),
        OpSpec(
            id="create_collection",
            label="Create Collection",
            method="PUT",
            path="{cluster_url}/collections/{collection}",
            visible_fields=["collection", "size", "distance"],
            body_builder=lambda v: {
                "vectors": {
                    "size": int(getattr(v, "size", 0) or 0),
                    "distance": getattr(v, "distance", None) or "Cosine",
                },
            },
        ),
        OpSpec(
            id="delete_collection",
            label="Delete Collection",
            method="DELETE",
            path="{cluster_url}/collections/{collection}",
            visible_fields=["collection"],
            success_payload_template={"deleted": True, "collection": "{collection}"},
        ),
        OpSpec(
            id="upsert_points",
            label="Upsert Points",
            method="PUT",
            path="{cluster_url}/collections/{collection}/points",
            visible_fields=["collection", "points"],
            body_builder=lambda v: {"points": getattr(v, "points", None) or []},
        ),
        OpSpec(
            id="search_points",
            label="Search Points",
            method="POST",
            path="{cluster_url}/collections/{collection}/points/search",
            visible_fields=[
                "collection",
                "vector",
                "limit",
                "filter",
                "with_payload",
                "with_vector",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "vector": getattr(v, "vector", None),
                    "limit": int(getattr(v, "limit", 10) or 10),
                    "filter": getattr(v, "filter", None),
                    "with_payload": bool(getattr(v, "with_payload", True)),
                    "with_vector": bool(getattr(v, "with_vector", False)),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_points",
            label="Delete Points",
            method="POST",
            path="{cluster_url}/collections/{collection}/points/delete",
            visible_fields=["collection", "ids", "filter"],
            body_builder=lambda v: (
                {"filter": v.filter}
                if getattr(v, "filter", None)
                else {"points": getattr(v, "ids", None) or []}
            ),
        ),
    ],
    outputs_schema=[
        {"label": "result", "type": "object"},
        {"label": "status", "type": "string"},
        {"label": "collections", "type": "array"},
    ],
    allow_error=True,
)
