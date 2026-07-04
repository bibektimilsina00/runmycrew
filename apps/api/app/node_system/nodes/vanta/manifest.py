"""Vanta action node — Vanta — compliance controls, findings, security tests.

REST at https://api.vanta.com/v1. See sim-parity roadmap Phase 4.30.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.vanta",
    name="Vanta",
    category="integration",
    description="Vanta — compliance controls, findings, security tests.",
    icon_slug="vanta",
    color="#1c1c1c",
    base_url="https://api.vanta.com/v1",
    credential_type="vanta_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="tailnet", label="Tailnet", type="string", default="-"),
        FieldSpec(name="device_id", label="Device ID", type="string"),
        FieldSpec(name="tags", label="Tags (JSON array)", type="json", default=[]),
        FieldSpec(name="s3_bucket", label="S3 Bucket", type="string"),
        FieldSpec(name="s3_key", label="S3 Key", type="string"),
        FieldSpec(
            name="feature_types",
            label="Feature Types (JSON)",
            type="json",
            default=["TABLES", "FORMS"],
        ),
        FieldSpec(name="pipeline_name", label="Pipeline Name", type="string"),
        FieldSpec(name="task_id", label="Task ID", type="string"),
        FieldSpec(name="run_id", label="Run ID", type="string"),
        FieldSpec(name="payload", label="Payload (JSON)", type="json", default={}),
        FieldSpec(name="test_id", label="Test ID", type="string"),
        FieldSpec(name="status", label="Status", type="string"),
        FieldSpec(name="event_ticker", label="Event Ticker", type="string"),
        FieldSpec(name="ticker", label="Ticker", type="string"),
        FieldSpec(name="side", label="Side (yes|no|buy|sell)", type="string"),
        FieldSpec(name="count", label="Count", type="number", default=1),
        FieldSpec(name="price", label="Yes Price (¢)", type="number", default=50),
        FieldSpec(name="condition_id", label="Condition ID", type="string"),
        FieldSpec(name="token_id", label="Token ID", type="string"),
        FieldSpec(name="fixture_id", label="Fixture ID", type="string"),
        FieldSpec(name="app_user_id", label="App User ID", type="string"),
        FieldSpec(name="entitlement_id", label="Entitlement ID", type="string"),
        FieldSpec(name="duration", label="Duration", type="string", default="monthly"),
    ],
    operations=[
        OpSpec(
            id="list_controls",
            label="List Controls",
            method="GET",
            path="/controls",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_findings",
            label="List Findings",
            method="GET",
            path="/findings",
            visible_fields=["status"],
            query_builder=lambda v: {
                k: val for k, val in {"status": getattr(v, "status", None) or None}.items() if val
            },
        ),
        OpSpec(
            id="list_tests",
            label="List Tests",
            method="GET",
            path="/tests",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_test",
            label="Get Test",
            method="GET",
            path="/tests/{test_id}",
            visible_fields=["test_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
