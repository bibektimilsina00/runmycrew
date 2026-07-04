"""Extend action node — Extend — document extraction (invoices, receipts, PDFs).

REST at https://api.extend.ai/v1. See sim-parity roadmap Phase 4.23.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.extend",
    name="Extend",
    category="integration",
    description="Extend — document extraction (invoices, receipts, PDFs).",
    icon_slug="extend",
    color="#1c1c1c",
    base_url="https://api.extend.ai/v1",
    credential_type="extend_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="meeting_id", label="Meeting ID", type="string"),
        FieldSpec(name="note_id", label="Note ID", type="string"),
        FieldSpec(name="note_guid", label="Note GUID", type="string"),
        FieldSpec(name="notebook_guid", label="Notebook GUID", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="content", label="Content", type="string"),
        FieldSpec(name="workflow_id", label="Workflow ID", type="string"),
        FieldSpec(name="run_id", label="Run ID", type="string"),
        FieldSpec(name="url", label="Document URL", type="string"),
        FieldSpec(name="calendar_api_id", label="Calendar API ID", type="string"),
        FieldSpec(name="api_id", label="Event API ID", type="string"),
        FieldSpec(name="guests", label="Guests (JSON array of {email, name})", type="json"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="process_document",
            label="Process Document",
            method="POST",
            path="/workflow_runs",
            visible_fields=["workflow_id", "url"],
            body_builder=lambda v: {
                "workflow_id": getattr(v, "workflow_id", "") or "",
                "file": {"url": getattr(v, "url", "") or ""},
            },
        ),
        OpSpec(
            id="get_run",
            label="Get Workflow Run",
            method="GET",
            path="/workflow_runs/{run_id}",
            visible_fields=["run_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_workflows",
            label="List Workflows",
            method="GET",
            path="/workflows",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
