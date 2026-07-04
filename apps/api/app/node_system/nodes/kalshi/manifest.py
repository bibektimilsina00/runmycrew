"""Kalshi action node — Kalshi — prediction market events, markets, orders.

REST at https://trading-api.kalshi.com/trade-api/v2. See sim-parity roadmap Phase 4.30.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.kalshi",
    name="Kalshi",
    category="integration",
    description="Kalshi — prediction market events, markets, orders.",
    icon_slug="kalshi",
    color="#1c1c1c",
    base_url="https://trading-api.kalshi.com/trade-api/v2",
    credential_type="kalshi_api_key",
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
            id="list_events",
            label="List Events",
            method="GET",
            path="/events",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_markets",
            label="List Markets",
            method="GET",
            path="/markets",
            visible_fields=["event_ticker"],
            query_builder=lambda v: {
                k: val
                for k, val in {"event_ticker": getattr(v, "event_ticker", None) or None}.items()
                if val
            },
        ),
        OpSpec(
            id="get_market",
            label="Get Market",
            method="GET",
            path="/markets/{ticker}",
            visible_fields=["ticker"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="place_order",
            label="Place Order",
            method="POST",
            path="/portfolio/orders",
            visible_fields=["ticker", "side", "count", "price"],
            body_builder=lambda v: {
                "ticker": getattr(v, "ticker", "") or "",
                "side": getattr(v, "side", "") or "",
                "count": int(getattr(v, "count", 1) or 1),
                "yes_price": int(getattr(v, "price", 50) or 50),
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
