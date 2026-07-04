"""Datadog action node — Datadog — metrics, logs, events, monitors.

REST at https://api.datadoghq.com/api/v2. See sim-parity roadmap Phase 4.20.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.datadog",
    name="Datadog",
    category="integration",
    description="Datadog — metrics, logs, events, monitors.",
    icon_slug="datadog",
    color="#1c1c1c",
    base_url="https://api.datadoghq.com/api/v2",
    credential_type="datadog_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="DD-API-KEY",
    extra_headers={"DD-APPLICATION-KEY": "{app_key}"},
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
            id="submit_metrics",
            label="Submit Metrics",
            method="POST",
            path="/series",
            visible_fields=["series"],
            body_builder=lambda v: {"series": getattr(v, "series", None) or []},
        ),
        OpSpec(
            id="submit_logs",
            label="Submit Logs",
            method="POST",
            path="/logs",
            visible_fields=["logs"],
            body_builder=lambda v: getattr(v, "logs", None) or [],
        ),
        OpSpec(
            id="submit_event",
            label="Submit Event",
            method="POST",
            path="/events",
            visible_fields=["title", "text", "tags"],
            body_builder=lambda v: {
                "data": {
                    "type": "event",
                    "attributes": {
                        "title": getattr(v, "title", "") or "",
                        "text": getattr(v, "text", "") or "",
                        "tags": [
                            t.strip()
                            for t in (getattr(v, "tags", "") or "").split(",")
                            if t.strip()
                        ],
                    },
                }
            },
        ),
        OpSpec(
            id="list_monitors",
            label="List Monitors",
            method="GET",
            path="/monitor",
            visible_fields=["query"],
            query_builder=lambda v: {
                k: val for k, val in {"query": getattr(v, "query", None) or None}.items() if val
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
