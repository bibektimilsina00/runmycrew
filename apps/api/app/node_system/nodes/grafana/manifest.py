"""Grafana Cloud action node — Grafana Cloud — dashboards, alerts, annotations, folders.

REST at https://{stack}.grafana.net/api. See sim-parity roadmap Phase 4.20.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.grafana",
    name="Grafana Cloud",
    category="integration",
    description="Grafana Cloud — dashboards, alerts, annotations, folders.",
    icon_slug="grafana",
    color="#1c1c1c",
    base_url="https://{stack}.grafana.net/api",
    credential_type="grafana_api_key",
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
            id="list_dashboards",
            label="List Dashboards",
            method="GET",
            path="/search",
            visible_fields=["query"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "query": getattr(v, "query", None) or None,
                    "type": "dash-db",
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_dashboard",
            label="Get Dashboard",
            method="GET",
            path="/dashboards/uid/{dashboard_uid}",
            visible_fields=["dashboard_uid"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_annotation",
            label="Create Annotation",
            method="POST",
            path="/annotations",
            visible_fields=["dashboard_id", "text", "tags"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "dashboardId": int(getattr(v, "dashboard_id", 0) or 0) or None,
                    "text": getattr(v, "text", None) or None,
                    "tags": [
                        t.strip() for t in (getattr(v, "tags", "") or "").split(",") if t.strip()
                    ]
                    or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_alerts",
            label="List Alert Rules",
            method="GET",
            path="/v1/provisioning/alert-rules",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
