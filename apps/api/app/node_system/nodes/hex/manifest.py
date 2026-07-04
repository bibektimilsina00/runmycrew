"""Hex action node — Hex — collaborative data notebooks + apps.

REST at https://app.hex.tech/api/v1. See sim-parity roadmap Phase 4.20.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.hex",
    name="Hex",
    category="integration",
    description="Hex — collaborative data notebooks + apps.",
    icon_slug="hex",
    color="#1c1c1c",
    base_url="https://app.hex.tech/api/v1",
    credential_type="hex_api_key",
    token_field=["api_key"],
    auth="bearer",
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
            id="run_project",
            label="Run Project",
            method="POST",
            path="/projects/{project_id}/runs",
            visible_fields=["project_id", "input_params", "dry_run"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "inputParams": getattr(v, "input_params", None) or None,
                    "dryRun": (getattr(v, "dry_run", None) or "false").lower() == "true"
                    if getattr(v, "dry_run", None) is not None
                    else None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_run_status",
            label="Get Run Status",
            method="GET",
            path="/projects/{project_id}/runs/{run_id}",
            visible_fields=["project_id", "run_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_projects",
            label="List Projects",
            method="GET",
            path="/projects",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="cancel_run",
            label="Cancel Run",
            method="DELETE",
            path="/projects/{project_id}/runs/{run_id}",
            visible_fields=["project_id", "run_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
