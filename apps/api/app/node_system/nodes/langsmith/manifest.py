"""LangSmith action node — LangSmith — LLM trace + evaluation platform.

REST at https://api.smith.langchain.com. See sim-parity roadmap Phase 4.20.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.langsmith",
    name="LangSmith",
    category="integration",
    description="LangSmith — LLM trace + evaluation platform.",
    icon_slug="langsmith",
    color="#1c1c1c",
    base_url="https://api.smith.langchain.com",
    credential_type="langsmith_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-API-Key",
    fields=[
        FieldSpec(name="series", label="Metric Series (JSON array)", type="json"),
        FieldSpec(name="logs", label="Log Entries (JSON array)", type="json"),
        FieldSpec(name="events", label="Events (JSON array)", type="json"),
        FieldSpec(name="identification", label="Identifications (JSON array)", type="json"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="text", label="Text / Message", type="string"),
        FieldSpec(name="tags", label="Tags (comma-separated)", type="string"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(name="nrql", label="NRQL Query", type="string"),
        FieldSpec(name="account_id", label="Account ID", type="string"),
        FieldSpec(name="chart_id", label="Chart ID", type="string"),
        FieldSpec(name="dashboard_id", label="Dashboard ID (numeric)", type="string"),
        FieldSpec(name="dashboard_uid", label="Dashboard UID", type="string"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="run_type", label="Run Type (chain/llm/tool)", type="string"),
        FieldSpec(name="inputs", label="Inputs (JSON)", type="json"),
        FieldSpec(name="project_name", label="Project / Session Name", type="string"),
        FieldSpec(name="project_id", label="Project ID", type="string"),
        FieldSpec(name="run_id", label="Run ID", type="string"),
        FieldSpec(name="key", label="Feedback Key", type="string"),
        FieldSpec(name="score", label="Score (float)", type="number"),
        FieldSpec(name="value", label="Value", type="string"),
        FieldSpec(name="input_params", label="Input Params (JSON)", type="json"),
        FieldSpec(name="dry_run", label="Dry Run (true/false)", type="string", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="create_run",
            label="Create Trace Run",
            method="POST",
            path="/runs",
            visible_fields=["name", "run_type", "inputs", "project_name"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "name": getattr(v, "name", None) or None,
                    "run_type": getattr(v, "run_type", None) or None,
                    "inputs": getattr(v, "inputs", None) or None,
                    "session_name": getattr(v, "project_name", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_runs",
            label="List Runs",
            method="POST",
            path="/runs/query",
            visible_fields=["project_name", "limit"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "session": [getattr(v, "project_name", "")]
                    if getattr(v, "project_name", None)
                    else None,
                    "limit": int(getattr(v, "limit", 100) or 100),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_datasets",
            label="List Datasets",
            method="GET",
            path="/datasets",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 100) or 100)},
        ),
        OpSpec(
            id="create_feedback",
            label="Create Feedback",
            method="POST",
            path="/feedback",
            visible_fields=["run_id", "key", "score", "value"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "run_id": getattr(v, "run_id", None) or None,
                    "key": getattr(v, "key", None) or None,
                    "score": float(getattr(v, "score", 0) or 0)
                    if getattr(v, "score", None) is not None
                    else None,
                    "value": getattr(v, "value", None) or None,
                }.items()
                if val is not None
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
