"""Fathom action node — manifest form.

Fathom.video REST API at `https://api.fathom.ai/external/v1`. Bearer
auth via `X-Api-Key` header (custom, not Authorization).

Meetings, action items, participants read-only.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.fathom",
    name="Fathom",
    category="integration",
    description="Fathom.video — meetings, transcripts, action items.",
    icon_slug="fathom",
    color="#1c1c1c",
    base_url="https://api.fathom.ai/external/v1",
    credential_type="fathom_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-Api-Key",
    fields=[
        FieldSpec(name="meeting_id", label="Meeting ID", type="string"),
        FieldSpec(name="from_date", label="From (ISO)", type="string"),
        FieldSpec(name="to_date", label="To (ISO)", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
        FieldSpec(name="cursor", label="Cursor", type="string", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_meetings",
            label="List Meetings",
            method="GET",
            path="/meetings",
            visible_fields=["from_date", "to_date", "limit", "cursor"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "from_date": getattr(v, "from_date", None),
                    "to_date": getattr(v, "to_date", None),
                    "limit": int(getattr(v, "limit", 50) or 50),
                    "cursor": getattr(v, "cursor", None),
                }.items()
                if val not in (None, "")
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
            id="get_transcript",
            label="Get Meeting Transcript",
            method="GET",
            path="/meetings/{meeting_id}/transcript",
            visible_fields=["meeting_id"],
        ),
        OpSpec(
            id="get_summary",
            label="Get Meeting Summary",
            method="GET",
            path="/meetings/{meeting_id}/summary",
            visible_fields=["meeting_id"],
        ),
        OpSpec(
            id="get_action_items",
            label="Get Action Items",
            method="GET",
            path="/meetings/{meeting_id}/action_items",
            visible_fields=["meeting_id"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "recording_url", "type": "string"},
        {"label": "meetings", "type": "array"},
        {"label": "transcript", "type": "array"},
        {"label": "action_items", "type": "array"},
        {"label": "next_cursor", "type": "string"},
    ],
    allow_error=True,
)
