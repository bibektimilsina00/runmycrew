"""Cursor-diff strategies for the polling-trigger scaffold.

Three pure functions cover ~80% of real polling triggers:

  - `diff_known_ids` — emit items whose id wasn't in the prior set.
    First poll snapshots silently; later polls fan out one execution
    per new id. Used for resources without a usable timestamp
    (subscribers, contacts, issues filtered by repo).
  - `diff_since_timestamp` — pass a `since=<ts>` to the API on
    subsequent calls; emit everything the server returns. First poll
    snapshots `now()`. Used for endpoints that natively support
    `since` filtering (GitHub `/issues/comments`, GitHub `/commits`).
  - `diff_last_sha` — alias for known-ids keyed on SHA. Same shape,
    different default cap (200 → 500 SHAs retained).

Anything that doesn't fit these (etag maps, nested history events, page-
token chains) drops down to a `CustomDiff` on the event manifest.

Every diff returns `(matches, new_cursor)` where `new_cursor` carries:
  - `event_type`: the manifest event id (so swapping events resets the diff)
  - `repo` or other identity scope passed in via `scope_key`
  - strategy-specific state
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utc_now_rfc3339() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _max_per(props: Any, default: int = 25, cap: int = 500) -> int:
    raw = getattr(props, "max_per_poll", None)
    try:
        n = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        n = default
    return max(1, min(n, cap))


def _flatten_each(
    items: list[dict[str, Any]], flatten_fn: Any, event_id: str
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        shaped = flatten_fn(item) if flatten_fn is not None else dict(item)
        shaped["event_type"] = event_id
        out.append(shaped)
    return out


def diff_known_ids(
    items: list[dict[str, Any]],
    cursor: dict[str, Any] | None,
    *,
    id_field: str,
    flatten_fn: Any,
    event_id: str,
    props: Any,
    scope: dict[str, Any] | None = None,
    retain: int = 500,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Emit items whose `id_field` isn't in the prior cursor's known set."""
    ids_now = [str(item.get(id_field)) for item in items if item.get(id_field) is not None]
    prior_ids = (cursor or {}).get("known_ids") if isinstance(cursor, dict) else None
    base_cursor: dict[str, Any] = {"event_type": event_id, **(scope or {})}

    if not isinstance(prior_ids, list):
        return [], {**base_cursor, "known_ids": ids_now[:retain]}

    known = set(prior_ids)
    matches: list[dict[str, Any]] = []
    emitted: set[str] = set()
    cap = _max_per(props)
    # Oldest first — newest items typically arrive at the head of the
    # response, so the first execution should carry the oldest unseen.
    for item in reversed(items):
        iid = str(item.get(id_field) or "")
        if not iid or iid in known:
            continue
        emitted.add(iid)
        if len(matches) < cap:
            matches.append(item)
    # We collect emitted ids regardless of `cap` so they don't fire
    # again on the next poll. The unemitted overflow is still recorded.
    shaped = _flatten_each(matches, flatten_fn, event_id)
    merged = list(known | emitted)
    if len(merged) > retain:
        merged = merged[-retain:]
    return shaped, {**base_cursor, "known_ids": merged}


def diff_since_timestamp(
    items: list[dict[str, Any]],
    cursor: dict[str, Any] | None,
    *,
    timestamp_field: str,
    flatten_fn: Any,
    event_id: str,
    props: Any,
    scope: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Use a `since` timestamp cursor — emit everything the server gave us,
    advance the cursor to the newest item's timestamp."""
    base_cursor: dict[str, Any] = {"event_type": event_id, **(scope or {})}
    prior_since = (cursor or {}).get("since") if isinstance(cursor, dict) else None

    if not prior_since:
        # First poll: snapshot now, emit nothing.
        return [], {**base_cursor, "since": _utc_now_rfc3339()}

    cap = _max_per(props)
    items_sorted = sorted(items, key=lambda i: str(i.get(timestamp_field) or ""))
    capped = items_sorted[:cap]
    newest = (items_sorted[-1].get(timestamp_field) if items_sorted else prior_since) or prior_since
    shaped = _flatten_each(capped, flatten_fn, event_id)
    return shaped, {**base_cursor, "since": str(newest)}


def diff_last_sha(
    items: list[dict[str, Any]],
    cursor: dict[str, Any] | None,
    *,
    flatten_fn: Any,
    event_id: str,
    props: Any,
    scope: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Same as `diff_known_ids` keyed on `sha`. Distinct entrypoint so
    the manifest reads cleanly — commits are conceptually sha-keyed,
    not id-keyed."""
    return diff_known_ids(
        items,
        cursor,
        id_field="sha",
        flatten_fn=flatten_fn,
        event_id=event_id,
        props=props,
        scope=scope,
        retain=500,
    )


__all__ = [
    "diff_known_ids",
    "diff_last_sha",
    "diff_since_timestamp",
]
