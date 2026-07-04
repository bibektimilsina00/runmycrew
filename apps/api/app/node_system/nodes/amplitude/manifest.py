"""Amplitude action node — Amplitude — product analytics event ingestion.

REST at https://api2.amplitude.com. See sim-parity roadmap Phase 4.20.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.amplitude",
    name="Amplitude",
    category="integration",
    description="Amplitude — product analytics event ingestion.",
    icon_slug="amplitude",
    color="#1c1c1c",
    base_url="https://api2.amplitude.com",
    credential_type="amplitude_api_key",
    token_field=["api_key"],
    auth="none",
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
            id="track_event",
            label="Track Event (HTTP API v2)",
            method="POST",
            path="/2/httpapi",
            visible_fields=["events"],
            body_builder=lambda v: {
                "api_key": (getattr(v, "_cred", None) or {}).get("api_key", ""),
                "events": getattr(v, "events", None) or [],
            },
        ),
        OpSpec(
            id="identify_user",
            label="Identify User",
            method="POST",
            path="/identify",
            visible_fields=["identification"],
            body_builder=lambda v: {
                "api_key": (getattr(v, "_cred", None) or {}).get("api_key", ""),
                "identification": getattr(v, "identification", None) or [],
            },
        ),
        OpSpec(
            id="chart_export",
            label="Chart Export",
            method="GET",
            path="/2/chart/{chart_id}/query",
            visible_fields=["chart_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
