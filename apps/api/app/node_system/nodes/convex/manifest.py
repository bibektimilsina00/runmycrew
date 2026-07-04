"""Convex action node — Convex — reactive backend / DB.

REST at {deployment_url}/api. See sim-parity roadmap Phase 4.21.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.convex",
    name="Convex",
    category="integration",
    description="Convex — reactive backend / DB.",
    icon_slug="convex",
    color="#1c1c1c",
    base_url="{deployment_url}/api",
    credential_type="convex_api_key",
    token_field=["api_key"],
    auth="bearer",
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
            id="run_query",
            label="Run Query Function",
            method="POST",
            path="/query",
            visible_fields=["function_name", "args"],
            body_builder=lambda v: {
                "path": getattr(v, "function_name", "") or "",
                "args": getattr(v, "args", None) or {},
            },
        ),
        OpSpec(
            id="run_mutation",
            label="Run Mutation",
            method="POST",
            path="/mutation",
            visible_fields=["function_name", "args"],
            body_builder=lambda v: {
                "path": getattr(v, "function_name", "") or "",
                "args": getattr(v, "args", None) or {},
            },
        ),
        OpSpec(
            id="run_action",
            label="Run Action",
            method="POST",
            path="/action",
            visible_fields=["function_name", "args"],
            body_builder=lambda v: {
                "path": getattr(v, "function_name", "") or "",
                "args": getattr(v, "args", None) or {},
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "result", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
