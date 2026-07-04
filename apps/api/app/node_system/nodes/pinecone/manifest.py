"""Pinecone action node — manifest form.

Pinecone splits into control plane (`https://api.pinecone.io`) for
index lifecycle and data plane (`https://{index_host}`) for upserts/
queries. We cover both via a single manifest:

  - Control plane (single base URL): list / describe / create / delete
    indexes, list collections.
  - Data plane (per-index host): vector upsert / query / fetch / delete.
    Uses `{index_host}` resolved from the credential — same pattern as
    Supabase's project_url.

Auth is the custom `Api-Key` header (not Bearer).
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.pinecone",
    name="Pinecone",
    category="integration",
    description="Pinecone vector database — manage indexes + upsert/query vectors.",
    icon_slug="pinecone",
    color="#1c1c1c",
    base_url="https://api.pinecone.io",
    credential_type="pinecone_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="Api-Key",
    fields=[
        FieldSpec(name="index_name", label="Index Name", type="string"),
        FieldSpec(name="dimension", label="Dimension", type="number", mode="advanced"),
        FieldSpec(
            name="metric",
            label="Metric",
            type="options",
            default="cosine",
            mode="advanced",
            options=[
                {"label": "cosine", "value": "cosine"},
                {"label": "dotproduct", "value": "dotproduct"},
                {"label": "euclidean", "value": "euclidean"},
            ],
        ),
        FieldSpec(name="cloud", label="Cloud", type="string", default="aws", mode="advanced"),
        FieldSpec(
            name="region", label="Region", type="string", default="us-east-1", mode="advanced"
        ),
        FieldSpec(name="namespace", label="Namespace", type="string", mode="advanced"),
        FieldSpec(name="vectors", label="Vectors (JSON array)", type="json"),
        FieldSpec(name="vector", label="Query Vector (JSON array)", type="json"),
        FieldSpec(name="ids", label="IDs (JSON array)", type="json"),
        FieldSpec(name="top_k", label="Top K", type="number", default=10, mode="advanced"),
        FieldSpec(
            name="include_values",
            label="Include vectors",
            type="boolean",
            default=False,
            mode="advanced",
        ),
        FieldSpec(
            name="include_metadata",
            label="Include metadata",
            type="boolean",
            default=True,
            mode="advanced",
        ),
        FieldSpec(name="filter", label="Filter (JSON)", type="json", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_indexes",
            label="List Indexes",
            method="GET",
            path="/indexes",
        ),
        OpSpec(
            id="describe_index",
            label="Describe Index",
            method="GET",
            path="/indexes/{index_name}",
            visible_fields=["index_name"],
        ),
        OpSpec(
            id="create_index",
            label="Create Index",
            method="POST",
            path="/indexes",
            visible_fields=["index_name", "dimension", "metric", "cloud", "region"],
            body_builder=lambda v: {
                "name": getattr(v, "index_name", None),
                "dimension": int(getattr(v, "dimension", 0) or 0),
                "metric": getattr(v, "metric", None) or "cosine",
                "spec": {
                    "serverless": {
                        "cloud": getattr(v, "cloud", None) or "aws",
                        "region": getattr(v, "region", None) or "us-east-1",
                    }
                },
            },
        ),
        OpSpec(
            id="delete_index",
            label="Delete Index",
            method="DELETE",
            path="/indexes/{index_name}",
            visible_fields=["index_name"],
            success_payload_template={"deleted": True, "name": "{index_name}"},
        ),
        OpSpec(
            id="upsert",
            label="Upsert Vectors",
            method="POST",
            path="https://{index_host}/vectors/upsert",
            visible_fields=["vectors", "namespace"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "vectors": getattr(v, "vectors", None) or [],
                    "namespace": getattr(v, "namespace", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="query",
            label="Query Vectors",
            method="POST",
            path="https://{index_host}/query",
            visible_fields=[
                "vector",
                "top_k",
                "namespace",
                "include_values",
                "include_metadata",
                "filter",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "vector": getattr(v, "vector", None),
                    "topK": int(getattr(v, "top_k", 10) or 10),
                    "namespace": getattr(v, "namespace", None),
                    "includeValues": bool(getattr(v, "include_values", False)),
                    "includeMetadata": bool(getattr(v, "include_metadata", True)),
                    "filter": getattr(v, "filter", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="fetch",
            label="Fetch by IDs",
            method="GET",
            path="https://{index_host}/vectors/fetch",
            visible_fields=["ids", "namespace"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "ids": getattr(v, "ids", None),
                    "namespace": getattr(v, "namespace", None),
                }.items()
                if val
            },
        ),
        OpSpec(
            id="delete_vectors",
            label="Delete Vectors",
            method="POST",
            path="https://{index_host}/vectors/delete",
            visible_fields=["ids", "namespace", "filter"],
            body_builder=lambda v: _delete_vectors_body(v),
        ),
    ],
    outputs_schema=[
        {"label": "indexes", "type": "array"},
        {"label": "matches", "type": "array"},
        {"label": "vectors", "type": "object"},
        {"label": "upserted_count", "type": "number"},
        {"label": "namespace", "type": "string"},
    ],
    allow_error=True,
)


def _delete_vectors_body(v: Any) -> dict[str, Any]:
    """Pinecone's delete body branches on filter vs id-list."""
    body: dict[str, Any] = {}
    if getattr(v, "namespace", None):
        body["namespace"] = v.namespace
    if getattr(v, "filter", None):
        body["filter"] = v.filter
    elif getattr(v, "ids", None):
        body["ids"] = v.ids
    else:
        body["deleteAll"] = True
    return body
