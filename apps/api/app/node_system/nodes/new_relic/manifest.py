"""New Relic action node — New Relic — APM, logs, metrics via NRQL + events.

REST at https://api.newrelic.com/v2. See sim-parity roadmap Phase 4.20.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.new_relic",
    name="New Relic",
    category="integration",
    description="New Relic — APM, logs, metrics via NRQL + events.",
    icon_slug="new_relic",
    color="#1c1c1c",
    base_url="https://api.newrelic.com/v2",
    credential_type="new_relic_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="Api-Key",
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
            id="nrql_query",
            label="NRQL Query",
            method="GET",
            path="/accounts/{account_id}/query",
            visible_fields=["account_id", "nrql"],
            query_builder=lambda v: {"nrql": getattr(v, "nrql", "") or ""},
        ),
        OpSpec(
            id="submit_event",
            label="Submit Custom Event",
            method="POST",
            path="/accounts/{account_id}/events",
            visible_fields=["account_id", "events"],
            body_builder=lambda v: getattr(v, "events", None) or [],
        ),
        OpSpec(
            id="list_applications",
            label="List Applications",
            method="GET",
            path="/applications.json",
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
