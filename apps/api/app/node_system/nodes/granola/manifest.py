"""Granola action node — Granola — AI meeting notes for Mac.

REST at https://api.granola.ai/v1. See sim-parity roadmap Phase 4.23.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.granola",
    name="Granola",
    category="integration",
    description="Granola — AI meeting notes for Mac.",
    icon_slug="granola",
    color="#1c1c1c",
    base_url="https://api.granola.ai/v1",
    credential_type="granola_api_key",
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
            id="list_notes",
            label="List Notes",
            method="GET",
            path="/notes",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="get_note",
            label="Get Note",
            method="GET",
            path="/notes/{note_id}",
            visible_fields=["note_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_transcript",
            label="Get Transcript",
            method="GET",
            path="/notes/{note_id}/transcript",
            visible_fields=["note_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
