"""Temporal Cloud action node — Temporal Cloud — workflow orchestration API.

REST at https://api.temporal.io/api/v1. See sim-parity roadmap Phase 4.21.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.temporal",
    name="Temporal Cloud",
    category="integration",
    description="Temporal Cloud — workflow orchestration API.",
    icon_slug="temporal",
    color="#1c1c1c",
    base_url="https://api.temporal.io/api/v1",
    credential_type="temporal_api_key",
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
            id="start_workflow",
            label="Start Workflow",
            method="POST",
            path="/namespaces/{namespace}/workflows/{workflow_id}",
            visible_fields=["namespace", "workflow_id", "workflow_type", "task_queue", "input"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "workflow_id": getattr(v, "workflow_id", None) or None,
                    "workflow_type": {"name": getattr(v, "workflow_type", "") or ""},
                    "task_queue": {"name": getattr(v, "task_queue", "") or ""},
                    "input": {"payloads": [getattr(v, "input", None) or {}]},
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="describe_workflow",
            label="Describe Workflow",
            method="GET",
            path="/namespaces/{namespace}/workflows/{workflow_id}",
            visible_fields=["namespace", "workflow_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="terminate_workflow",
            label="Terminate Workflow",
            method="POST",
            path="/namespaces/{namespace}/workflows/{workflow_id}/terminate",
            visible_fields=["namespace", "workflow_id", "reason"],
            body_builder=lambda v: {"reason": getattr(v, "reason", "") or ""},
        ),
        OpSpec(
            id="list_workflows",
            label="List Workflows",
            method="GET",
            path="/namespaces/{namespace}/workflows",
            visible_fields=["namespace", "query"],
            query_builder=lambda v: {
                k: val for k, val in {"query": getattr(v, "query", None) or None}.items() if val
            },
        ),
        OpSpec(
            id="signal_workflow",
            label="Signal Workflow",
            method="POST",
            path="/namespaces/{namespace}/workflows/{workflow_id}/signal/{signal_name}",
            visible_fields=["namespace", "workflow_id", "signal_name", "input"],
            body_builder=lambda v: {"input": {"payloads": [getattr(v, "input", None) or {}]}},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "result", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
