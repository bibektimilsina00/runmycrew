"""ClickHouse Cloud action node — ClickHouse Cloud — analytics DB via HTTP interface.

REST at https://{host}. See sim-parity roadmap Phase 4.21.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.clickhouse",
    name="ClickHouse Cloud",
    category="integration",
    description="ClickHouse Cloud — analytics DB via HTTP interface.",
    icon_slug="clickhouse",
    color="#ffffff",
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
        FieldSpec(
            name="database",
            label="Database",
            type="string",
            remote=RemoteLookup(provider="clickhouse", resource="databases"),
        ),
        FieldSpec(
            name="table",
            label="Table",
            type="string",
            remote=RemoteLookup(
                provider="clickhouse",
                resource="tables",
                params={"database": "${database}"},
                depends_on=["database"],
            ),
        ),
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
        FieldSpec(name="query_text", label="Query", type="string"),
        FieldSpec(name="insert_body", label="Insert Body (JSON rows)", type="json", default={}),
        FieldSpec(name="query_id", label="Query ID", type="string"),
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
        OpSpec(
            id="list_databases",
            label="List Databases",
            method="POST",
            path="/",
            visible_fields=["query_text"],
            query_builder=lambda v: {"query": "SHOW DATABASES FORMAT JSON"},
        ),
        OpSpec(
            id="list_tables",
            label="List Tables",
            method="POST",
            path="/",
            visible_fields=["database"],
            query_builder=lambda v: {
                "query": "SHOW TABLES FROM "
                + (getattr(v, "database", "") or "default")
                + " FORMAT JSON"
            },
        ),
        OpSpec(
            id="describe_table",
            label="Describe Table",
            method="POST",
            path="/",
            visible_fields=["table"],
            query_builder=lambda v: {
                "query": "DESCRIBE TABLE " + (getattr(v, "table", "") or "") + " FORMAT JSON"
            },
        ),
        OpSpec(
            id="count",
            label="Row Count",
            method="POST",
            path="/",
            visible_fields=["table"],
            query_builder=lambda v: {
                "query": "SELECT count() FROM " + (getattr(v, "table", "") or "") + " FORMAT JSON"
            },
        ),
        OpSpec(
            id="truncate_table",
            label="Truncate Table",
            method="POST",
            path="/",
            visible_fields=["table"],
            query_builder=lambda v: {"query": "TRUNCATE TABLE " + (getattr(v, "table", "") or "")},
        ),
        OpSpec(
            id="drop_table",
            label="Drop Table",
            method="POST",
            path="/",
            visible_fields=["table"],
            query_builder=lambda v: {"query": "DROP TABLE " + (getattr(v, "table", "") or "")},
        ),
        OpSpec(
            id="optimize_table",
            label="Optimize Table",
            method="POST",
            path="/",
            visible_fields=["table"],
            query_builder=lambda v: {"query": "OPTIMIZE TABLE " + (getattr(v, "table", "") or "")},
        ),
        OpSpec(
            id="list_users",
            label="List Users",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SELECT * FROM system.users FORMAT JSON"},
        ),
        OpSpec(
            id="get_settings",
            label="Get System Settings",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SELECT * FROM system.settings FORMAT JSON"},
        ),
        OpSpec(
            id="show_create_table",
            label="SHOW CREATE TABLE",
            method="POST",
            path="/",
            visible_fields=["table"],
            query_builder=lambda v: {
                "query": "SHOW CREATE TABLE " + (getattr(v, "table", "") or "") + " FORMAT JSON"
            },
        ),
        OpSpec(
            id="create_database",
            label="CREATE DATABASE",
            method="POST",
            path="/",
            visible_fields=["database"],
            query_builder=lambda v: {
                "query": "CREATE DATABASE IF NOT EXISTS " + (getattr(v, "database", "") or "")
            },
        ),
        OpSpec(
            id="drop_database",
            label="DROP DATABASE",
            method="POST",
            path="/",
            visible_fields=["database"],
            query_builder=lambda v: {
                "query": "DROP DATABASE IF EXISTS " + (getattr(v, "database", "") or "")
            },
        ),
        OpSpec(
            id="show_processes",
            label="SHOW PROCESSLIST",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SHOW PROCESSLIST FORMAT JSON"},
        ),
        OpSpec(
            id="list_clusters",
            label="List Clusters",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SELECT * FROM system.clusters FORMAT JSON"},
        ),
        OpSpec(
            id="list_replicas",
            label="List Replicas",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SELECT * FROM system.replicas FORMAT JSON"},
        ),
        OpSpec(
            id="list_parts",
            label="List Parts",
            method="POST",
            path="/",
            visible_fields=["table"],
            query_builder=lambda v: {
                "query": "SELECT * FROM system.parts WHERE table = '"
                + (getattr(v, "table", "") or "")
                + "' FORMAT JSON"
            },
        ),
        OpSpec(
            id="list_mutations",
            label="List Mutations",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SELECT * FROM system.mutations FORMAT JSON"},
        ),
        OpSpec(
            id="kill_query",
            label="KILL QUERY",
            method="POST",
            path="/",
            visible_fields=["query_id"],
            query_builder=lambda v: {
                "query": "KILL QUERY WHERE query_id = '" + (getattr(v, "query_id", "") or "") + "'"
            },
        ),
        OpSpec(
            id="check_health",
            label="Health Check",
            method="GET",
            path="/ping",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_dictionaries",
            label="List Dictionaries",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SELECT * FROM system.dictionaries FORMAT JSON"},
        ),
        OpSpec(
            id="list_functions",
            label="List Functions",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SELECT * FROM system.functions FORMAT JSON"},
        ),
        OpSpec(
            id="list_columns",
            label="List Columns",
            method="POST",
            path="/",
            visible_fields=["table"],
            query_builder=lambda v: {
                "query": "SELECT * FROM system.columns WHERE table = '"
                + (getattr(v, "table", "") or "")
                + "' FORMAT JSON"
            },
        ),
        OpSpec(
            id="get_version",
            label="Get Version",
            method="POST",
            path="/",
            visible_fields=[],
            query_builder=lambda v: {"query": "SELECT version() FORMAT JSON"},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "result", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
