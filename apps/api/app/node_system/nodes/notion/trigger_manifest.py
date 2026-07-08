"""Notion polling trigger — manifest form.

Notion's REST idiom: `/query` endpoints are POST-only, and the
search API is a separate top-level POST. Custom paginate_fn routes
by event id.

Events (poll-observable subset of sim's 8):
  - `new_page`               — new pages in a target database
  - `page_updated`           — pages with fresh last_edited_time
  - `page_content_updated`   — alias for page_updated (semantic clarity)
  - `new_comment`            — comments on a specific page
  - `new_database`           — new databases created in the workspace

Not in polling (need webhook):
  page_deleted, database_deleted, database_schema_updated (Notion's
  API surfaces "archived" but not schema-history events).

Notion's `filter`/`sorts` on `/databases/{id}/query` sort by
last_edited_time desc so new + updated pages both come in at the top.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.nodes.notion import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template

_NOTION_VERSION = "2022-06-28"


def _title_from_page(page: dict) -> str:
    """Notion pages have a `properties` map — the title property
    varies per DB but there is exactly one type=title entry."""
    props = page.get("properties") or {}
    for _name, spec in props.items():
        if isinstance(spec, dict) and spec.get("type") == "title":
            parts = spec.get("title") or []
            text = "".join((p.get("plain_text") or "") for p in parts if isinstance(p, dict))
            if text:
                return text
    return ""


def _title_from_database(db: dict) -> str:
    """Databases carry title as an array of rich_text items."""
    parts = db.get("title") or []
    return "".join((p.get("plain_text") or "") for p in parts if isinstance(p, dict))


def _text_from_comment(comment: dict) -> str:
    parts = comment.get("rich_text") or []
    return "".join((p.get("plain_text") or "") for p in parts if isinstance(p, dict))


def _flatten_page(item):
    return {
        "id": item.get("id"),
        "title": _title_from_page(item),
        "url": item.get("url"),
        "created_time": item.get("created_time"),
        "last_edited_time": item.get("last_edited_time"),
        "archived": item.get("archived"),
        "parent": item.get("parent"),
        "properties": item.get("properties"),
    }


def _flatten_comment(item):
    parent = item.get("parent") or {}
    author = item.get("created_by") or {}
    return {
        "id": item.get("id"),
        "text": _text_from_comment(item),
        "created_time": item.get("created_time"),
        "last_edited_time": item.get("last_edited_time"),
        "page_id": parent.get("page_id") or parent.get("block_id"),
        "author_id": author.get("id"),
        "discussion_id": item.get("discussion_id"),
    }


def _flatten_database(item):
    return {
        "id": item.get("id"),
        "title": _title_from_database(item),
        "url": item.get("url"),
        "created_time": item.get("created_time"),
        "last_edited_time": item.get("last_edited_time"),
        "archived": item.get("archived"),
        "properties": item.get("properties"),
    }


register_flatten("notion.page", _flatten_page)
register_flatten("notion.comment", _flatten_comment)
register_flatten("notion.database", _flatten_database)


async def _walk_notion(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Route by event id. Notion's endpoints:

    - database pages: POST /databases/{id}/query
    - comments on page: GET /comments?block_id={page_id}
    - new databases: POST /search with {filter: {value: 'database'}}
    """
    headers = {
        "Authorization": f"Bearer {token or ''}",
        "Notion-Version": _NOTION_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    page_size_raw = getattr(props, "page_size", 25)
    try:
        page_size = max(1, min(int(page_size_raw or 25), 100))
    except (TypeError, ValueError):
        page_size = 25

    if event.id in ("new_page", "page_updated", "page_content_updated"):
        database_id = resolve_template("{database_id}", props) or ""
        if not database_id:
            return []
        url = f"{manifest.base_url}/databases/{database_id}/query"
        body = {
            "sorts": [{"timestamp": "last_edited_time", "direction": "descending"}],
            "page_size": page_size,
        }
        resp = await client.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        results = payload.get("results")
        return results if isinstance(results, list) else []

    if event.id == "new_comment":
        page_id = resolve_template("{page_id}", props) or ""
        if not page_id:
            return []
        url = f"{manifest.base_url}/comments"
        params = {"block_id": page_id, "page_size": page_size}
        resp = await client.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        results = payload.get("results")
        return results if isinstance(results, list) else []

    if event.id == "new_database":
        url = f"{manifest.base_url}/search"
        body = {
            "filter": {"property": "object", "value": "database"},
            "sort": {"direction": "descending", "timestamp": "last_edited_time"},
            "page_size": page_size,
        }
        resp = await client.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        payload = resp.json() or {}
        results = payload.get("results")
        return results if isinstance(results, list) else []

    return []


MANIFEST = PollingTriggerManifest(
    type="trigger.notion",
    name=NAME,
    description=(
        "Poll a Notion database for new / updated pages, a page for new "
        "comments, or the workspace for new databases."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.notion.com/v1",
    credential_type=["notion_oauth", "notion_api_key"],
    token_field=["access_token", "api_key"],
    auth="bearer",
    extra_headers={"Notion-Version": _NOTION_VERSION},
    provider="notion",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="database_id",
            label="Database ID (for page events / new_database ignored)",
            type="string",
        ),
        FieldSpec(
            name="page_id",
            label="Page ID (for new_comment event)",
            type="string",
        ),
        FieldSpec(
            name="page_size",
            label="Page Size",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_page",
            label="Page Added to Database",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="notion.page",
            extra_fields=["database_id"],
        ),
        PollingEvent(
            id="page_updated",
            label="Page Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="last_edited_time",
            flatten="notion.page",
            extra_fields=["database_id"],
        ),
        PollingEvent(
            id="page_content_updated",
            label="Page Content Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="last_edited_time",
            flatten="notion.page",
            extra_fields=["database_id"],
        ),
        PollingEvent(
            id="new_comment",
            label="New Comment on Page",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="notion.comment",
            extra_fields=["page_id"],
        ),
        PollingEvent(
            id="new_database",
            label="New Database Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="notion.database",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "last_edited_time", "type": "string"},
        {"label": "created_time", "type": "string"},
        {"label": "text", "type": "string"},
        {"label": "page_id", "type": "string"},
    ],
    paginate_fn=_walk_notion,
)
