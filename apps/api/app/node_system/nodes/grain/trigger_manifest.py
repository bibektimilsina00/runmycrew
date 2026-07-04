"""Grain polling trigger — manifest form.

Watches Grain for new recordings, highlights, or stories.

Events (5 poll-observable of sim's 7):
  - `recording_created`  — known_ids on recording id
  - `recording_updated`  — since_timestamp on updated_datetime
  - `highlight_created`  — known_ids on highlight id
  - `highlight_updated`  — since_timestamp on updated_datetime
  - `story_created`      — known_ids on story id

Not in polling (need webhook):
  item_added, item_updated (Grain's "view" abstraction — server-side
  filter changes surface only via webhook events).
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_recording(item):
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "url": item.get("url"),
        "public_url": item.get("public_url"),
        "start_datetime": item.get("start_datetime"),
        "end_datetime": item.get("end_datetime"),
        "created_datetime": item.get("created_datetime"),
        "updated_datetime": item.get("updated_datetime"),
        "workspace_id": item.get("workspace_id"),
        "owner_name": (item.get("owners") or [{}])[0].get("name")
        if isinstance(item.get("owners"), list) and item.get("owners")
        else None,
        "participants": [
            (p.get("name") or p.get("email"))
            for p in (item.get("participants") or [])
            if isinstance(p, dict)
        ],
    }


def _flatten_highlight(item):
    return {
        "id": item.get("id"),
        "text": item.get("text"),
        "recording_id": item.get("recording_id"),
        "timestamp": item.get("timestamp"),
        "duration": item.get("duration"),
        "url": item.get("url"),
        "thumbnail_url": item.get("thumbnail_url"),
        "created_datetime": item.get("created_datetime"),
        "updated_datetime": item.get("updated_datetime"),
        "created_by_name": (item.get("created_by") or {}).get("name"),
    }


def _flatten_story(item):
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "url": item.get("url"),
        "public_url": item.get("public_url"),
        "created_datetime": item.get("created_datetime"),
        "updated_datetime": item.get("updated_datetime"),
        "highlight_count": len(item.get("highlights") or [])
        if isinstance(item.get("highlights"), list)
        else None,
    }


register_flatten("grain.recording", _flatten_recording)
register_flatten("grain.highlight", _flatten_highlight)
register_flatten("grain.story", _flatten_story)


MANIFEST = PollingTriggerManifest(
    type="trigger.grain",
    name="Grain",
    description=("Poll Grain for new / updated recordings, highlights, or new stories."),
    icon_slug="grain",
    color="#1c1c1c",
    base_url="https://api.grain.com/_/public-api",
    credential_type="grain_api_key",
    token_field=["api_key"],
    auth="bearer",
    provider="grain",
    default_poll_interval_seconds=90,
    events=[
        PollingEvent(
            id="recording_created",
            label="Recording Created",
            list_path="/v3/recordings",
            strategy="known_ids",
            id_field="id",
            flatten="grain.recording",
        ),
        PollingEvent(
            id="recording_updated",
            label="Recording Updated",
            list_path="/v3/recordings",
            strategy="since_timestamp",
            timestamp_field="updated_datetime",
            flatten="grain.recording",
        ),
        PollingEvent(
            id="highlight_created",
            label="Highlight Created",
            list_path="/v3/highlights",
            strategy="known_ids",
            id_field="id",
            flatten="grain.highlight",
        ),
        PollingEvent(
            id="highlight_updated",
            label="Highlight Updated",
            list_path="/v3/highlights",
            strategy="since_timestamp",
            timestamp_field="updated_datetime",
            flatten="grain.highlight",
        ),
        PollingEvent(
            id="story_created",
            label="Story Created",
            list_path="/v3/stories",
            strategy="known_ids",
            id_field="id",
            flatten="grain.story",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "text", "type": "string"},
        {"label": "recording_id", "type": "string"},
        {"label": "created_datetime", "type": "string"},
        {"label": "updated_datetime", "type": "string"},
    ],
)
