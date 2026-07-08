"""Databricks action node — Databricks — SQL warehouses, jobs, notebooks.

REST at {workspace_url}/api/2.0. See sim-parity roadmap Phase 4.21.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.databricks",
    name="Databricks",
    category="integration",
    description="Databricks — SQL warehouses, jobs, notebooks.",
    icon_slug="databricks",
    color="#ffffff",
    base_url="{workspace_url}/api/2.0",
    credential_type="databricks_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="warehouse_id",
            label="SQL Warehouse",
            type="string",
            remote=RemoteLookup(provider="databricks", resource="warehouses"),
        ),
        FieldSpec(name="statement", label="SQL Statement", type="string"),
        FieldSpec(name="statement_id", label="Statement ID", type="string"),
        FieldSpec(
            name="catalog",
            label="Catalog",
            type="string",
            remote=RemoteLookup(provider="databricks", resource="catalogs"),
        ),
        FieldSpec(
            name="schema_name",
            label="Schema",
            type="string",
            remote=RemoteLookup(
                provider="databricks",
                resource="schemas",
                params={"catalog": "${catalog}"},
                depends_on=["catalog"],
            ),
        ),
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
            id="run_sql",
            label="Run SQL Statement",
            method="POST",
            path="/sql/statements/",
            visible_fields=["warehouse_id", "statement", "catalog", "schema"],
            body_builder=lambda v: {
                "warehouse_id": getattr(v, "warehouse_id", "") or "",
                "statement": getattr(v, "statement", "") or "",
                "catalog": getattr(v, "catalog", None) or None,
                "schema": getattr(v, "schema_name", None) or None,
                "wait_timeout": "30s",
            },
        ),
        OpSpec(
            id="get_statement",
            label="Get Statement Status",
            method="GET",
            path="/sql/statements/{statement_id}",
            visible_fields=["statement_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="run_job",
            label="Run Job",
            method="POST",
            path="/jobs/run-now",
            visible_fields=["job_id", "parameters"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "job_id": int(getattr(v, "job_id", 0) or 0) or None,
                    "notebook_params": getattr(v, "parameters", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_run",
            label="Get Job Run",
            method="GET",
            path="/jobs/runs/get",
            visible_fields=["run_id"],
            query_builder=lambda v: {"run_id": getattr(v, "run_id", "") or ""},
        ),
        OpSpec(
            id="list_warehouses",
            label="List SQL Warehouses",
            method="GET",
            path="/sql/warehouses",
            visible_fields=[],
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
