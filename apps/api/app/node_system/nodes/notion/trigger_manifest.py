"""Notion polling trigger — manifest form.

Watches a Notion database for new / updated pages. The database
`/query` endpoint is POST-only (Notion's REST idiom), so we drop
down to a custom paginate_fn that issues the POST with the right
`Notion-Version` header + Bearer auth.

Notion's `filter`/`sorts` bodies would let us bound the poll to
`last_edited_time` server-side, but the general shape works client-side
too via `since_timestamp` on the sorted list.
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

_NOTION_VERSION = "2022-06-28"


def _title_from_page(page: dict) -> str:
    """Notion pages have a `properties` map — the title property
    varies per DB but there is exactly one type=title entry. Pull it
    out for a friendlier flattened payload."""
    props = page.get("properties") or {}
    for _name, spec in props.items():
        if isinstance(spec, dict) and spec.get("type") == "title":
            parts = spec.get("title") or []
            text = "".join((p.get("plain_text") or "") for p in parts if isinstance(p, dict))
            if text:
                return text
    return ""


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


register_flatten("notion.page", _flatten_page)


async def _walk_notion(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """POST to /databases/{database_id}/query with sort by last_edited_time
    descending. One page (page_size items) is enough for polling — new
    pages come in at the top."""
    database_id = resolve_template("{database_id}", props) or ""
    if not database_id:
        return []
    url = f"{manifest.base_url}/databases/{database_id}/query"
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
    body = {
        "sorts": [{"timestamp": "last_edited_time", "direction": "descending"}],
        "page_size": page_size,
    }
    resp = await client.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    payload = resp.json() or {}
    results = payload.get("results")
    return results if isinstance(results, list) else []


MANIFEST = PollingTriggerManifest(
    type="trigger.notion",
    name="Notion",
    description="Poll a Notion database for new or updated pages.",
    icon_slug="notion",
    color="#1c1c1c",
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
            label="Database ID",
            type="string",
            required=True,
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
            list_path="/databases/{database_id}/query",
            strategy="known_ids",
            id_field="id",
            flatten="notion.page",
        ),
        PollingEvent(
            id="page_updated",
            label="Page Updated",
            list_path="/databases/{database_id}/query",
            strategy="since_timestamp",
            timestamp_field="last_edited_time",
            flatten="notion.page",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "last_edited_time", "type": "string"},
        {"label": "created_time", "type": "string"},
    ],
    paginate_fn=_walk_notion,
)
