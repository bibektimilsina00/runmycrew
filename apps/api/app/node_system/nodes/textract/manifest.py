"""AWS Textract action node — AWS Textract — OCR + form/table extraction for documents.

REST at https://textract.{region}.amazonaws.com. See sim-parity roadmap Phase 4.30.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.textract",
    name="AWS Textract",
    category="integration",
    description="AWS Textract — OCR + form/table extraction for documents.",
    icon_slug="textract",
    color="#232F3E",
    base_url="https://textract.{region}.amazonaws.com",
    credential_type="aws_credentials",
    token_field=["api_key"],
    auth="aws_sigv4",
    aws_service="textract",
    extra_headers={"Content-Type": "application/x-amz-json-1.1"},
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
            id="detect_document_text",
            label="Detect Document Text",
            method="POST",
            path="/",
            visible_fields=["s3_bucket", "s3_key"],
            body_builder=lambda v: {
                "Document": {
                    "S3Object": {
                        "Bucket": getattr(v, "s3_bucket", "") or "",
                        "Name": getattr(v, "s3_key", "") or "",
                    }
                }
            },
        ),
        OpSpec(
            id="analyze_document",
            label="Analyze Document",
            method="POST",
            path="/",
            visible_fields=["s3_bucket", "s3_key", "feature_types"],
            body_builder=lambda v: {
                "Document": {
                    "S3Object": {
                        "Bucket": getattr(v, "s3_bucket", "") or "",
                        "Name": getattr(v, "s3_key", "") or "",
                    }
                },
                "FeatureTypes": getattr(v, "feature_types", None) or ["TABLES", "FORMS"],
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
