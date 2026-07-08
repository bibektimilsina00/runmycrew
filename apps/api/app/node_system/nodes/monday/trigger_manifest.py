"""Monday.com polling trigger — manifest form.

Monday.com is GraphQL-only; the scaffold's default GET-based fetcher
doesn't fit. Custom paginate_fn issues a GraphQL POST against
`https://api.monday.com/v2` with an items_page query for the target
board.

Auth: raw key in `Authorization` (no `Bearer` prefix — same convention
as Linear).

Sim spec surfaces 9 events (item_created, item_deleted, item_moved,
item_name_changed, item_archived, status_changed, column_changed,
subitem_created, update_created). Monday.com is GraphQL-first and
doesn't expose per-event lists — every event derives from board state
diffs. We ship 6 that map cleanly to polling:

  - `new_item` — known_ids diff on board items
  - `item_updated` — since_timestamp on updated_at
  - `item_moved` — group_id change per item (custom diff)
  - `status_changed` — status column value change per item (custom diff)
  - `column_changed` — any column value change per item (custom diff)
  - `new_update` — known_ids diff on board updates

`item_deleted` + `subitem_created` + `item_archived` + `item_name_changed`
need webhook delivery to be usable (a poller can't observe deletes
retrospectively). Note in the description so users know to expect the
gap.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.nodes.monday import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template

_MONDAY_API = "https://api.monday.com/v2"

# Fetch items with the column values we compare against for the
# custom-diff events. `column_values.id` + `column_values.value` are
# the raw JSON-encoded value strings Monday.com returns.
_ITEMS_QUERY = """
query BoardItems($boardId: ID!, $limit: Int!) {
  boards(ids: [$boardId]) {
    items_page(limit: $limit) {
      items {
        id name state created_at updated_at
        group { id title }
        column_values { id text value column { id title type } }
        creator { id name email }
      }
    }
  }
}
"""

_UPDATES_QUERY = """
query BoardUpdates($boardId: ID!, $limit: Int!) {
  boards(ids: [$boardId]) {
    updates(limit: $limit) {
      id body text_body created_at updated_at
      creator { id name email }
      item_id
    }
  }
}
"""


def _flatten_item(item):
    group = item.get("group") or {}
    creator = item.get("creator") or {}
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "state": item.get("state"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "group_id": group.get("id"),
        "group_title": group.get("title"),
        "creator_name": creator.get("name"),
        "creator_email": creator.get("email"),
        "column_values": item.get("column_values"),
    }


def _flatten_update(item):
    creator = item.get("creator") or {}
    return {
        "id": item.get("id"),
        "body": item.get("body"),
        "text_body": item.get("text_body"),
        "created_at": item.get("created_at"),
        "item_id": item.get("item_id"),
        "creator_name": creator.get("name"),
        "creator_email": creator.get("email"),
    }


register_flatten("monday.item", _flatten_item)
register_flatten("monday.update", _flatten_update)


# ── custom diff handlers ─────────────────────────────────────────────


def _extract_status(item: dict[str, Any]) -> str:
    """Pull the first status-type column value off an item. Monday
    boards typically have one canonical status column — if there are
    multiple, we still emit one event per change on any of them."""
    for col in item.get("column_values") or []:
        if isinstance(col, dict) and (col.get("column") or {}).get("type") == "status":
            return str(col.get("text") or col.get("value") or "")
    return ""


def _extract_group(item: dict[str, Any]) -> str:
    return str((item.get("group") or {}).get("id") or "")


def _extract_column_fingerprint(item: dict[str, Any]) -> str:
    """Hash-free serialization of every column value on the item.
    Cheaper than a real hash for the row counts we deal with (≤50)
    and diff-stable across polls."""
    parts: list[str] = []
    for col in item.get("column_values") or []:
        if isinstance(col, dict):
            parts.append(f"{col.get('id')}={col.get('text') or col.get('value') or ''}")
    return "|".join(sorted(parts))


def _diff_by_field(items, cursor, props, event_id, field_extractor, event_key):
    """Generic per-item-field diff. `field_extractor(item)` returns the
    watched value; if it differs from what we saw last poll for that
    id, emit the flattened item.

    Cursor shape: `{event_type, board_id, values: {item_id: last_seen}}`.
    First poll snapshots silently — otherwise every existing row
    fires on first activation, flooding the workflow."""
    board_id = str(getattr(props, "board_id", "") or "")
    prior = None
    if (
        isinstance(cursor, dict)
        and cursor.get("event_type") == event_id
        and cursor.get("board_id") == board_id
    ):
        prior = cursor.get("values")
    new_values: dict[str, str] = {}
    matches: list[dict[str, Any]] = []
    first_poll = prior is None
    for item in items:
        item_id = str(item.get("id") or "")
        if not item_id:
            continue
        current = field_extractor(item)
        new_values[item_id] = current
        if first_poll:
            continue
        prev = prior.get(item_id) if isinstance(prior, dict) else None
        if prev is not None and prev != current:
            flat = _flatten_item(item)
            flat["event_type"] = event_id
            flat["change"] = {"key": event_key, "from": prev, "to": current}
            matches.append(flat)
    new_cursor: dict[str, Any] = {
        "event_type": event_id,
        "board_id": board_id,
        "values": new_values,
    }
    return matches, new_cursor


def _diff_status(items, cursor, props, event_id):
    return _diff_by_field(items, cursor, props, event_id, _extract_status, "status")


def _diff_group(items, cursor, props, event_id):
    return _diff_by_field(items, cursor, props, event_id, _extract_group, "group")


def _diff_columns(items, cursor, props, event_id):
    return _diff_by_field(items, cursor, props, event_id, _extract_column_fingerprint, "columns")


# ── paginator ───────────────────────────────────────────────────────


async def _walk_monday(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """One GraphQL POST per poll. Two queries — items vs. updates —
    routed by event id. Board id lives in the common fields; we
    template it into the variables."""
    board_id = resolve_template("{board_id}", props) or ""
    if not board_id:
        return []
    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 200))
    except (TypeError, ValueError):
        limit = 25
    headers = {
        "Authorization": token or "",
        "API-Version": "2024-10",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    is_update = event.id == "new_update"
    query = _UPDATES_QUERY if is_update else _ITEMS_QUERY
    resp = await client.post(
        _MONDAY_API,
        headers=headers,
        json={
            "query": query,
            "variables": {"boardId": board_id, "limit": limit},
        },
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message") or "Monday GraphQL error")
    data = payload.get("data") or {}
    boards = data.get("boards") or []
    if not boards:
        return []
    board = boards[0] or {}
    if is_update:
        return board.get("updates") or []
    return ((board.get("items_page") or {}).get("items")) or []


# ── manifest ────────────────────────────────────────────────────────


MANIFEST = PollingTriggerManifest(
    type="trigger.monday",
    name=NAME,
    description=(
        "Poll a Monday.com board for new items, item changes (status / "
        "group / column), and new updates. Note: item_deleted / archived "
        "aren't observable via polling — attach a Monday webhook for "
        "those."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.monday.com",
    credential_type="monday_api_key",
    token_field=["api_key"],
    auth="header_token",
    provider="monday",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="board_id",
            label="Board ID",
            type="string",
            required=True,
        ),
    ],
    events=[
        PollingEvent(
            id="new_item",
            label="New Item",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="monday.item",
        ),
        PollingEvent(
            id="item_updated",
            label="Item Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated_at",
            flatten="monday.item",
        ),
        PollingEvent(
            id="status_changed",
            label="Status Changed",
            list_path="",
            diff_handler=_diff_status,
        ),
        PollingEvent(
            id="item_moved",
            label="Item Moved to Group",
            list_path="",
            diff_handler=_diff_group,
        ),
        PollingEvent(
            id="column_changed",
            label="Column Value Changed",
            list_path="",
            diff_handler=_diff_columns,
        ),
        PollingEvent(
            id="new_update",
            label="New Update / Comment",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="monday.update",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "state", "type": "string"},
        {"label": "group_id", "type": "string"},
        {"label": "group_title", "type": "string"},
        {"label": "created_at", "type": "string"},
        {"label": "updated_at", "type": "string"},
        {"label": "column_values", "type": "array"},
        {"label": "change", "type": "object"},
    ],
    paginate_fn=_walk_monday,
)
