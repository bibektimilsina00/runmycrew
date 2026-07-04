"""Luma action node — Luma — events + calendars via lu.ma.

REST at https://api.lu.ma/public/v1. See sim-parity roadmap Phase 4.23.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.luma",
    name="Luma",
    category="integration",
    description="Luma — events + calendars via lu.ma.",
    icon_slug="luma",
    color="#1c1c1c",
    base_url="https://api.lu.ma/public/v1",
    credential_type="luma_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="x-luma-api-key",
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
            id="list_events",
            label="List Events",
            method="GET",
            path="/calendar/list-events",
            visible_fields=["calendar_api_id"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "calendar_api_id": getattr(v, "calendar_api_id", None) or None
                }.items()
                if val
            },
        ),
        OpSpec(
            id="get_event",
            label="Get Event",
            method="GET",
            path="/event/get",
            visible_fields=["api_id"],
            query_builder=lambda v: {"api_id": getattr(v, "api_id", "") or ""},
        ),
        OpSpec(
            id="list_guests",
            label="List Event Guests",
            method="GET",
            path="/event/get-guests",
            visible_fields=["api_id"],
            query_builder=lambda v: {"api_id": getattr(v, "api_id", "") or ""},
        ),
        OpSpec(
            id="add_guests",
            label="Add Guests to Event",
            method="POST",
            path="/event/add-guests",
            visible_fields=["api_id", "guests"],
            body_builder=lambda v: {
                "event_api_id": getattr(v, "api_id", "") or "",
                "guests": getattr(v, "guests", None) or [],
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
