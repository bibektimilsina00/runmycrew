"""ClickHouse Cloud action node — ClickHouse Cloud — analytics DB via HTTP interface.

REST at https://{host}. See sim-parity roadmap Phase 4.21.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.clickhouse",
    name="ClickHouse Cloud",
    category="integration",
    description="ClickHouse Cloud — analytics DB via HTTP interface.",
    icon_slug="clickhouse",
    color="#1c1c1c",
    base_url="https://{host}",
    credential_type="clickhouse_api_key",
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
            id="query",
            label="Run Query",
            method="POST",
            path="/",
            visible_fields=["sql", "database"],
            body_builder=lambda v: getattr(v, "sql", "") or "",
        ),
        OpSpec(
            id="insert",
            label="Insert Rows (JSON)",
            method="POST",
            path="/",
            visible_fields=["table", "database", "rows"],
            body_builder=lambda v: str(getattr(v, "rows", "")) or "",
        ),
        OpSpec(
            id="show_tables",
            label="Show Tables",
            method="POST",
            path="/",
            visible_fields=["database"],
            body_builder=lambda v: "SHOW TABLES",
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "result", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
