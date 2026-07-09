"""Luma action node — Luma — events + calendars via lu.ma.

REST at https://api.lu.ma/public/v1. See sim-parity roadmap Phase 4.23.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.luma",
    name="Luma",
    category="integration",
    description="Luma — events + calendars via lu.ma.",
    icon_slug="luma",
    color="#ffffff",
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
        FieldSpec(name="luma_event_api_id", label="Event API ID", type="string"),
        FieldSpec(name="luma_event_body", label="Event Body (JSON)", type="json", default={}),
        FieldSpec(name="luma_slug", label="Event Slug", type="string"),
        FieldSpec(name="luma_guest_email", label="Guest Email", type="string"),
        FieldSpec(name="luma_guests_body", label="Guests Body (JSON)", type="json", default={}),
        FieldSpec(
            name="luma_guest_status", label="Guest Status (approved|declined|going)", type="string"
        ),
        FieldSpec(
            name="luma_invite_emails", label="Invite Emails (JSON array)", type="json", default=[]
        ),
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
        OpSpec(
            id="create_event",
            label="Create Event",
            method="POST",
            path="/public/v1/event/create",
            visible_fields=["luma_event_body"],
            body_builder=lambda v: getattr(v, "luma_event_body", None) or {},
        ),
        OpSpec(
            id="update_event",
            label="Update Event",
            method="POST",
            path="/public/v1/event/update",
            visible_fields=["luma_event_api_id", "luma_event_body"],
            body_builder=lambda v: {
                "api_id": getattr(v, "luma_event_api_id", "") or "",
                **(getattr(v, "luma_event_body", None) or {}),
            },
        ),
        OpSpec(
            id="lookup_event",
            label="Lookup Event by Slug",
            method="GET",
            path="/public/v1/event/lookup",
            visible_fields=["luma_slug"],
            query_builder=lambda v: {"slug": getattr(v, "luma_slug", "") or ""},
        ),
        OpSpec(
            id="cancel_event",
            label="Cancel Event",
            method="POST",
            path="/public/v1/event/cancel",
            visible_fields=["luma_event_api_id"],
            body_builder=lambda v: {"api_id": getattr(v, "luma_event_api_id", "") or ""},
        ),
        OpSpec(
            id="get_guests",
            label="Get Event Guests",
            method="GET",
            path="/public/v1/event/get-guests",
            visible_fields=["luma_event_api_id"],
            query_builder=lambda v: {"event_api_id": getattr(v, "luma_event_api_id", "") or ""},
        ),
        OpSpec(
            id="get_guest",
            label="Get Guest",
            method="GET",
            path="/public/v1/event/get-guest",
            visible_fields=["luma_event_api_id", "luma_guest_email"],
            query_builder=lambda v: {
                "event_api_id": getattr(v, "luma_event_api_id", "") or "",
                "email": getattr(v, "luma_guest_email", "") or "",
            },
        ),
        OpSpec(
            id="send_invites",
            label="Send Invites",
            method="POST",
            path="/public/v1/event/send-invites",
            visible_fields=["luma_event_api_id", "luma_invite_emails"],
            body_builder=lambda v: {
                "event_api_id": getattr(v, "luma_event_api_id", "") or "",
                "guests": getattr(v, "luma_invite_emails", []) or [],
            },
        ),
        OpSpec(
            id="update_guest_status",
            label="Update Guest Status",
            method="POST",
            path="/public/v1/event/update-guest-status",
            visible_fields=["luma_event_api_id", "luma_guest_email", "luma_guest_status"],
            body_builder=lambda v: {
                "event_api_id": getattr(v, "luma_event_api_id", "") or "",
                "email": getattr(v, "luma_guest_email", "") or "",
                "status": getattr(v, "luma_guest_status", "") or "",
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
