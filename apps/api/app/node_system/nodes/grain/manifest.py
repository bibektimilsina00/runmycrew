"""Grain action node — manifest form.

Grain public API v3 at `https://api.grain.com/_/public-api/v3`.
Bearer auth via a personal access token.

6 ops cover the typical workflow: list / get recordings,
list highlights, list stories, list users, get single item.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.grain",
    name="Grain",
    category="integration",
    description="Grain — meetings, recordings, highlights, stories.",
    icon_slug="grain",
    color="#1c1c1c",
    base_url="https://api.grain.com/_/public-api",
    credential_type="grain_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="recording_id", label="Recording ID", type="string"),
        FieldSpec(name="highlight_id", label="Highlight ID", type="string"),
        FieldSpec(name="story_id", label="Story ID", type="string"),
        FieldSpec(
            name="cursor",
            label="Pagination Cursor",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="limit",
            label="Limit",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="list_recordings",
            label="List Recordings",
            method="GET",
            path="/v3/recordings",
            visible_fields=["cursor", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "cursor": getattr(v, "cursor", None) or None,
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_recording",
            label="Get Recording",
            method="GET",
            path="/v3/recordings/{recording_id}",
            visible_fields=["recording_id"],
        ),
        OpSpec(
            id="list_highlights",
            label="List Highlights",
            method="GET",
            path="/v3/highlights",
            visible_fields=["cursor", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "cursor": getattr(v, "cursor", None) or None,
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_highlight",
            label="Get Highlight",
            method="GET",
            path="/v3/highlights/{highlight_id}",
            visible_fields=["highlight_id"],
        ),
        OpSpec(
            id="list_stories",
            label="List Stories",
            method="GET",
            path="/v3/stories",
            visible_fields=["cursor", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "cursor": getattr(v, "cursor", None) or None,
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_story",
            label="Get Story",
            method="GET",
            path="/v3/stories/{story_id}",
            visible_fields=["story_id"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "start_datetime", "type": "string"},
        {"label": "end_datetime", "type": "string"},
        {"label": "recordings", "type": "array"},
        {"label": "highlights", "type": "array"},
        {"label": "stories", "type": "array"},
    ],
    allow_error=True,
)
