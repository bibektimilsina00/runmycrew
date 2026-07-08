"""Zoom action node — manifest form.

Zoom REST API at `https://api.zoom.us/v2`. Bearer auth via
zoom_oauth credential. Meeting + user + recording ops.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.zoom",
    name="Zoom",
    category="integration",
    description="Zoom — meetings, users, recordings.",
    icon_slug="zoom",
    color="#ffffff",
    base_url="https://api.zoom.us/v2",
    credential_type="zoom_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="user_id",
            label="User",
            type="string",
            default="me",
            remote=RemoteLookup(provider="zoom", resource="users"),
        ),
        FieldSpec(
            name="meeting_id",
            label="Meeting",
            type="string",
            remote=RemoteLookup(provider="zoom", resource="meetings"),
        ),
        FieldSpec(name="topic", label="Topic", type="string"),
        FieldSpec(
            name="meeting_type",
            label="Type",
            type="options",
            default="2",
            mode="advanced",
            options=[
                {"label": "Instant", "value": "1"},
                {"label": "Scheduled", "value": "2"},
                {"label": "Recurring (no fixed time)", "value": "3"},
                {"label": "Recurring (fixed time)", "value": "8"},
            ],
        ),
        FieldSpec(name="start_time", label="Start Time (ISO)", type="string"),
        FieldSpec(name="duration", label="Duration (minutes)", type="number", mode="advanced"),
        FieldSpec(name="timezone", label="Timezone", type="string", default="UTC", mode="advanced"),
        FieldSpec(name="agenda", label="Agenda", type="string", mode="advanced"),
        FieldSpec(name="password", label="Password", type="string", secret=True, mode="advanced"),
        FieldSpec(name="settings", label="Settings (JSON)", type="json", mode="advanced"),
        FieldSpec(
            name="meeting_status",
            label="Meeting Status",
            type="options",
            mode="advanced",
            default="scheduled",
            options=[
                {"label": "scheduled", "value": "scheduled"},
                {"label": "live", "value": "live"},
                {"label": "upcoming", "value": "upcoming"},
            ],
        ),
        FieldSpec(name="page_size", label="Page Size", type="number", default=30, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="get_user",
            label="Get User",
            method="GET",
            path="/users/{user_id}",
            visible_fields=["user_id"],
        ),
        OpSpec(
            id="list_meetings",
            label="List Meetings",
            method="GET",
            path="/users/{user_id}/meetings",
            visible_fields=["user_id", "meeting_status", "page_size"],
            query_builder=lambda v: {
                "type": getattr(v, "meeting_status", None) or "scheduled",
                "page_size": int(getattr(v, "page_size", 30) or 30),
            },
        ),
        OpSpec(
            id="get_meeting",
            label="Get Meeting",
            method="GET",
            path="/meetings/{meeting_id}",
            visible_fields=["meeting_id"],
        ),
        OpSpec(
            id="create_meeting",
            label="Create Meeting",
            method="POST",
            path="/users/{user_id}/meetings",
            visible_fields=[
                "user_id",
                "topic",
                "meeting_type",
                "start_time",
                "duration",
                "timezone",
                "agenda",
                "password",
                "settings",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "topic": getattr(v, "topic", None),
                    "type": int(getattr(v, "meeting_type", None) or 2),
                    "start_time": getattr(v, "start_time", None),
                    "duration": int(getattr(v, "duration", 0) or 0) or None,
                    "timezone": getattr(v, "timezone", None) or "UTC",
                    "agenda": getattr(v, "agenda", None),
                    "password": getattr(v, "password", None),
                    "settings": getattr(v, "settings", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="update_meeting",
            label="Update Meeting",
            method="PATCH",
            path="/meetings/{meeting_id}",
            visible_fields=["meeting_id", "topic", "start_time", "duration", "agenda", "settings"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "topic": getattr(v, "topic", None),
                    "start_time": getattr(v, "start_time", None),
                    "duration": int(getattr(v, "duration", 0) or 0) or None,
                    "agenda": getattr(v, "agenda", None),
                    "settings": getattr(v, "settings", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_meeting",
            label="Delete Meeting",
            method="DELETE",
            path="/meetings/{meeting_id}",
            visible_fields=["meeting_id"],
            success_payload_template={"deleted": True, "id": "{meeting_id}"},
        ),
        OpSpec(
            id="list_recordings",
            label="List User Recordings",
            method="GET",
            path="/users/{user_id}/recordings",
            visible_fields=["user_id", "page_size"],
            query_builder=lambda v: {"page_size": int(getattr(v, "page_size", 30) or 30)},
        ),
        OpSpec(
            id="get_meeting_recordings",
            label="Get Meeting Recordings",
            method="GET",
            path="/meetings/{meeting_id}/recordings",
            visible_fields=["meeting_id"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "number"},
        {"label": "topic", "type": "string"},
        {"label": "join_url", "type": "string"},
        {"label": "start_url", "type": "string"},
        {"label": "meetings", "type": "array"},
        {"label": "recording_files", "type": "array"},
    ],
    allow_error=True,
)
