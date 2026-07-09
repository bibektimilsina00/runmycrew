"""Apify action node — manifest form.

Apify's REST API at `https://api.apify.com/v2`. Bearer auth using a
personal API token. Ops cover the actor lifecycle (run + status +
results) and dataset/key-value-store access.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.apify",
    name="Apify",
    category="integration",
    description="Apify — run actors, fetch datasets, manage key-value stores.",
    icon_slug="apify",
    color="#ffffff",
    base_url="https://api.apify.com/v2",
    credential_type="apify_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="actor_id",
            label="Actor",
            type="string",
            placeholder="username~actor-name or actorId",
            remote=RemoteLookup(provider="apify", resource="actors"),
        ),
        FieldSpec(name="run_id", label="Run ID", type="string"),
        FieldSpec(
            name="dataset_id",
            label="Dataset",
            type="string",
            remote=RemoteLookup(provider="apify", resource="datasets"),
        ),
        FieldSpec(name="store_id", label="Key-Value Store ID", type="string"),
        FieldSpec(name="key", label="Key", type="string"),
        FieldSpec(name="input", label="Actor Input (JSON)", type="json"),
        FieldSpec(name="value", label="Value", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
        FieldSpec(name="offset", label="Offset", type="number", default=0, mode="advanced"),
        FieldSpec(
            name="clean",
            label="Clean Items",
            type="boolean",
            default=True,
            mode="advanced",
            description="Strip metadata fields from dataset items.",
        ),
    ],
    operations=[
        OpSpec(
            id="run_actor",
            label="Run Actor (sync)",
            method="POST",
            path="/acts/{actor_id}/run-sync-get-dataset-items",
            visible_fields=["actor_id", "input"],
            body_builder=lambda v: getattr(v, "input", None) or {},
        ),
        OpSpec(
            id="start_run",
            label="Start Run (async)",
            method="POST",
            path="/acts/{actor_id}/runs",
            visible_fields=["actor_id", "input"],
            body_builder=lambda v: getattr(v, "input", None) or {},
        ),
        OpSpec(
            id="get_run",
            label="Get Run",
            method="GET",
            path="/actor-runs/{run_id}",
            visible_fields=["run_id"],
        ),
        OpSpec(
            id="abort_run",
            label="Abort Run",
            method="POST",
            path="/actor-runs/{run_id}/abort",
            visible_fields=["run_id"],
        ),
        OpSpec(
            id="list_actors",
            label="List Actors",
            method="GET",
            path="/acts",
            visible_fields=["limit", "offset"],
            query_fields=["limit", "offset"],
        ),
        OpSpec(
            id="get_dataset_items",
            label="Get Dataset Items",
            method="GET",
            path="/datasets/{dataset_id}/items",
            visible_fields=["dataset_id", "limit", "offset", "clean"],
            query_builder=lambda v: {
                "limit": int(getattr(v, "limit", 100) or 100),
                "offset": int(getattr(v, "offset", 0) or 0),
                "clean": "true" if getattr(v, "clean", True) else "false",
                "format": "json",
            },
        ),
        OpSpec(
            id="get_store_record",
            label="Get Store Record",
            method="GET",
            path="/key-value-stores/{store_id}/records/{key}",
            visible_fields=["store_id", "key"],
        ),
        OpSpec(
            id="put_store_record",
            label="Put Store Record",
            method="PUT",
            path="/key-value-stores/{store_id}/records/{key}",
            visible_fields=["store_id", "key", "value"],
            body_builder=lambda v: getattr(v, "value", None),
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "items", "type": "array"},
        {"label": "data", "type": "object"},
        {"label": "defaultDatasetId", "type": "string"},
        {"label": "defaultKeyValueStoreId", "type": "string"},
    ],
    allow_error=True,
)
