"""Elasticsearch action node — Elasticsearch — index, search, aggregate documents.

REST at {host}. See sim-parity roadmap Phase 4.21.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.elasticsearch",
    name="Elasticsearch",
    category="integration",
    description="Elasticsearch — index, search, aggregate documents.",
    icon_slug="elasticsearch",
    color="#1c1c1c",
    base_url="{host}",
    credential_type="elasticsearch_api_key",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{username}",
    fields=[
        FieldSpec(name="warehouse_id", label="SQL Warehouse ID", type="string"),
        FieldSpec(name="statement", label="SQL Statement", type="string"),
        FieldSpec(name="statement_id", label="Statement ID", type="string"),
        FieldSpec(name="catalog", label="Catalog", type="string"),
        FieldSpec(name="schema_name", label="Schema", type="string"),
        FieldSpec(name="job_id", label="Job ID", type="string"),
        FieldSpec(name="run_id", label="Run ID", type="string"),
        FieldSpec(name="parameters", label="Parameters (JSON)", type="json"),
        FieldSpec(name="sql", label="SQL", type="string"),
        FieldSpec(name="database", label="Database", type="string"),
        FieldSpec(name="table", label="Table", type="string"),
        FieldSpec(name="rows", label="Rows (JSONEachRow)", type="string"),
        FieldSpec(name="index", label="Index", type="string"),
        FieldSpec(name="doc_id", label="Doc ID", type="string"),
        FieldSpec(name="document", label="Document (JSON)", type="json"),
        FieldSpec(name="query", label="Query (JSON / DSL / KQL)", type="json"),
        FieldSpec(name="function_name", label="Function Path", type="string"),
        FieldSpec(name="args", label="Function Args (JSON)", type="json"),
        FieldSpec(name="namespace", label="Namespace", type="string"),
        FieldSpec(name="workflow_id", label="Workflow ID", type="string"),
        FieldSpec(name="workflow_type", label="Workflow Type", type="string"),
        FieldSpec(name="task_queue", label="Task Queue", type="string"),
        FieldSpec(name="input", label="Input (JSON)", type="json"),
        FieldSpec(name="signal_name", label="Signal Name", type="string"),
        FieldSpec(name="reason", label="Reason", type="string"),
    ],
    operations=[
        OpSpec(
            id="search",
            label="Search",
            method="POST",
            path="/{index}/_search",
            visible_fields=["index", "query"],
            body_builder=lambda v: getattr(v, "query", None) or {"query": {"match_all": {}}},
        ),
        OpSpec(
            id="index_document",
            label="Index Document",
            method="POST",
            path="/{index}/_doc",
            visible_fields=["index", "document"],
            body_builder=lambda v: getattr(v, "document", None) or {},
        ),
        OpSpec(
            id="get_document",
            label="Get Document",
            method="GET",
            path="/{index}/_doc/{doc_id}",
            visible_fields=["index", "doc_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="delete_document",
            label="Delete Document",
            method="DELETE",
            path="/{index}/_doc/{doc_id}",
            visible_fields=["index", "doc_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="count",
            label="Count Documents",
            method="GET",
            path="/{index}/_count",
            visible_fields=["index"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "result", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
