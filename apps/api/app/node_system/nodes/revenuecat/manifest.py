"""RevenueCat action node — RevenueCat — subscribers, entitlements, offerings.

REST at https://api.revenuecat.com/v1. See sim-parity roadmap Phase 4.30.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.revenuecat",
    name="RevenueCat",
    category="integration",
    description="RevenueCat — subscribers, entitlements, offerings.",
    icon_slug="revenuecat",
    color="#ffffff",
    base_url="https://api.revenuecat.com/v1",
    credential_type="revenuecat_api_key",
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
            id="get_subscriber",
            label="Get Subscriber",
            method="GET",
            path="/subscribers/{app_user_id}",
            visible_fields=["app_user_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="grant_entitlement",
            label="Grant Entitlement",
            method="POST",
            path="/subscribers/{app_user_id}/entitlements/{entitlement_id}/promotional",
            visible_fields=["app_user_id", "entitlement_id", "duration"],
            body_builder=lambda v: {"duration": getattr(v, "duration", None) or "monthly"},
        ),
        OpSpec(
            id="revoke_entitlement",
            label="Revoke Promo Entitlement",
            method="DELETE",
            path="/subscribers/{app_user_id}/entitlements/{entitlement_id}/revoke_promotionals",
            visible_fields=["app_user_id", "entitlement_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="delete_subscriber",
            label="Delete Subscriber",
            method="DELETE",
            path="/subscribers/{app_user_id}",
            visible_fields=["app_user_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
