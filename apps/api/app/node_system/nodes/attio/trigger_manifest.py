"""Attio polling trigger — manifest form.

Attio v2 REST at `https://api.attio.com/v2`. Bearer auth. The scaffold's
default GET fetcher doesn't fit most endpoints — Attio's list APIs are
POST with a query body. Custom paginate_fn routes by event id.

Events (poll-observable subset of sim's 21):
  - `record_created`         — new records on a target object
  - `record_updated`         — records changed since last poll
  - `list_entry_created`     — new entries on a target list
  - `list_entry_updated`     — list entries changed
  - `note_created`           — notes attached to a record
  - `task_created`           — tasks under the workspace
  - `task_updated`           — tasks with changed status
  - `comment_created`        — comments on threads
  - `workspace_member_added` — new workspace members

Not in polling (need webhooks):
  *_deleted (10 events), *_resolved / *_unresolved (comments),
  record_merged, list_updated, note_updated — no updated_at surface
  on some payload types, or delete-only signals.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template


def _pull_id(item: dict) -> str:
    """Attio wraps every entity's id under `id.record_id` / `id.entry_id` /
    `id.task_id` / etc. — pull whichever key is present so the scaffold's
    known_ids diff has a stable string to key on."""
    id_obj = item.get("id") or {}
    if isinstance(id_obj, dict):
        for k in (
            "record_id",
            "entry_id",
            "note_id",
            "task_id",
            "comment_id",
            "member_id",
            "workspace_member_id",
        ):
            if id_obj.get(k):
                return str(id_obj[k])
    if isinstance(id_obj, str):
        return id_obj
    return ""


def _flatten_record(item):
    values = item.get("values") or {}
    # Attio value shape: {field_slug: [{active_from, active_until, value/..., ...}]}
    # We surface field_slug → first-value pairs so downstream nodes see
    # a flat dict without knowing Attio's array-of-versions envelope.
    flat_values: dict[str, Any] = {}
    for slug, versions in values.items():
        if isinstance(versions, list) and versions:
            v = versions[0]
            if isinstance(v, dict):
                # Attribute types carry different value keys — email
                # under `email_address`, number under `value`, etc.
                for key in ("value", "email_address", "phone_number", "target_record", "option"):
                    if key in v and v[key] is not None:
                        flat_values[slug] = v[key]
                        break
                else:
                    flat_values[slug] = v
    return {
        "id": _pull_id(item),
        "object_slug": (item.get("id") or {}).get("object_slug"),
        "workspace_id": (item.get("id") or {}).get("workspace_id"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at") or item.get("last_updated_at"),
        "web_url": item.get("web_url"),
        "values": flat_values,
    }


def _flatten_list_entry(item):
    return {
        "id": _pull_id(item),
        "list_id": (item.get("id") or {}).get("list_id"),
        "parent_record_id": item.get("parent_record_id"),
        "parent_object": item.get("parent_object"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "entry_values": item.get("entry_values"),
    }


def _flatten_note(item):
    return {
        "id": _pull_id(item),
        "parent_object": item.get("parent_object"),
        "parent_record_id": item.get("parent_record_id"),
        "title": item.get("title"),
        "content_plaintext": item.get("content_plaintext"),
        "created_at": item.get("created_at"),
        "created_by_actor": (item.get("created_by_actor") or {}).get("id"),
    }


def _flatten_task(item):
    return {
        "id": _pull_id(item),
        "content_plaintext": item.get("content_plaintext"),
        "is_completed": item.get("is_completed"),
        "deadline_at": item.get("deadline_at"),
        "linked_records": item.get("linked_records"),
        "assignees": item.get("assignees"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def _flatten_comment(item):
    return {
        "id": _pull_id(item),
        "thread_id": item.get("thread_id"),
        "content_plaintext": item.get("content_plaintext"),
        "author": (item.get("author") or {}).get("id"),
        "created_at": item.get("created_at"),
        "resolved_at": item.get("resolved_at"),
        "entry": item.get("entry"),
    }


def _flatten_member(item):
    return {
        "id": _pull_id(item),
        "first_name": item.get("first_name"),
        "last_name": item.get("last_name"),
        "email_address": item.get("email_address"),
        "access_level": item.get("access_level"),
        "created_at": item.get("created_at"),
    }


register_flatten("attio.record", _flatten_record)
register_flatten("attio.list_entry", _flatten_list_entry)
register_flatten("attio.note", _flatten_note)
register_flatten("attio.task", _flatten_task)
register_flatten("attio.comment", _flatten_comment)
register_flatten("attio.member", _flatten_member)


def _stamp_ids(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Hoist Attio's compound `id.record_id`/`entry_id`/etc. to a flat
    top-level `id` string so `known_ids` diff has a stable key. The
    scaffold reads `item[id_field]` — we can't ask it to walk into a
    nested `id` object."""
    for item in items:
        stable = _pull_id(item)
        if stable:
            item["id"] = stable
    return items


async def _walk_attio(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Route by event id — Attio's list surface is POST-based with
    per-endpoint filter/sort bodies."""
    headers = {
        "Authorization": f"Bearer {token or ''}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    base = manifest.base_url
    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 500))
    except (TypeError, ValueError):
        limit = 25

    # Common sort — desc on updated_at so newest come in first.
    sort_desc = [{"attribute": "updated_at", "direction": "desc"}]

    if event.id in ("record_created", "record_updated"):
        object_slug = resolve_template("{object_slug}", props) or ""
        if not object_slug:
            return []
        url = f"{base}/objects/{object_slug}/records/query"
        body = {"limit": limit, "sorts": sort_desc}
        resp = await client.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        items = payload.get("data") or []
        return _stamp_ids(items)

    if event.id in ("list_entry_created", "list_entry_updated"):
        list_id = resolve_template("{list_id}", props) or ""
        if not list_id:
            return []
        url = f"{base}/lists/{list_id}/entries/query"
        body = {"limit": limit, "sorts": sort_desc}
        resp = await client.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        items = payload.get("data") or []
        return _stamp_ids(items)

    if event.id == "note_created":
        # `/v2/notes` — GET with query params. Optional record_id filter.
        url = f"{base}/notes"
        params: dict[str, Any] = {"limit": limit}
        record_id = resolve_template("{record_id}", props) or ""
        if record_id:
            params["parent_record_id"] = record_id
        resp = await client.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        items = payload.get("data") or []
        return _stamp_ids(items)

    if event.id in ("task_created", "task_updated"):
        url = f"{base}/tasks"
        params = {"limit": limit}
        resp = await client.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        items = payload.get("data") or []
        return _stamp_ids(items)

    if event.id == "comment_created":
        # `/v2/comments` — GET with optional thread_id filter.
        url = f"{base}/comments"
        params = {"limit": limit}
        thread_id = resolve_template("{thread_id}", props) or ""
        if thread_id:
            params["thread_id"] = thread_id
        resp = await client.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        items = payload.get("data") or []
        return _stamp_ids(items)

    if event.id == "workspace_member_added":
        url = f"{base}/workspace_members"
        params = {"limit": limit}
        resp = await client.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        items = payload.get("data") or []
        return _stamp_ids(items)

    return []


MANIFEST = PollingTriggerManifest(
    type="trigger.attio",
    name="Attio",
    description=(
        "Poll Attio for new records, list entries, notes, tasks, comments, "
        "or workspace members. Attio hosts custom object schemas — pick "
        "which object_slug or list_id to watch per event."
    ),
    icon_slug="attio",
    color="#1c1c1c",
    base_url="https://api.attio.com/v2",
    credential_type="attio_api_key",
    token_field=["api_key"],
    auth="bearer",
    provider="attio",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="object_slug",
            label="Object slug (for record events)",
            type="string",
            placeholder="people | companies | deals | ...",
        ),
        FieldSpec(
            name="list_id",
            label="List ID (for list entry events)",
            type="string",
        ),
        FieldSpec(
            name="record_id",
            label="Record ID (optional; for note_created scope)",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="thread_id",
            label="Thread ID (optional; for comment_created scope)",
            type="string",
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="record_created",
            label="Record Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="attio.record",
            extra_fields=["object_slug"],
        ),
        PollingEvent(
            id="record_updated",
            label="Record Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated_at",
            flatten="attio.record",
            extra_fields=["object_slug"],
        ),
        PollingEvent(
            id="list_entry_created",
            label="List Entry Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="attio.list_entry",
            extra_fields=["list_id"],
        ),
        PollingEvent(
            id="list_entry_updated",
            label="List Entry Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated_at",
            flatten="attio.list_entry",
            extra_fields=["list_id"],
        ),
        PollingEvent(
            id="note_created",
            label="Note Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="attio.note",
            extra_fields=["record_id"],
        ),
        PollingEvent(
            id="task_created",
            label="Task Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="attio.task",
        ),
        PollingEvent(
            id="task_updated",
            label="Task Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated_at",
            flatten="attio.task",
        ),
        PollingEvent(
            id="comment_created",
            label="Comment Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="attio.comment",
            extra_fields=["thread_id"],
        ),
        PollingEvent(
            id="workspace_member_added",
            label="Workspace Member Added",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="attio.member",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "object_slug", "type": "string"},
        {"label": "list_id", "type": "string"},
        {"label": "created_at", "type": "string"},
        {"label": "updated_at", "type": "string"},
        {"label": "values", "type": "object"},
        {"label": "content_plaintext", "type": "string"},
        {"label": "web_url", "type": "string"},
    ],
    paginate_fn=_walk_attio,
)
