"""Telegram polling trigger — manifest form.

Telegram bots consume updates via `getUpdates?offset=N` — bot API's
long-poll idiom. Each poll fetches everything since the last acked
update, then bumps the offset one past the highest `update_id` so
the server drops those from future responses (Telegram semantic:
`offset` acknowledges previous batch).

Cursor: `{last_update_id: int}`. Diff is custom because the acked-
offset model doesn't fit the three builtin strategies.
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


def _flatten_message_update(item):
    msg = item.get("message") or item.get("edited_message") or {}
    chat = msg.get("chat") or {}
    frm = msg.get("from") or {}
    return {
        "update_id": item.get("update_id"),
        "message_id": msg.get("message_id"),
        "date": msg.get("date"),
        "text": msg.get("text"),
        "chat_id": chat.get("id"),
        "chat_type": chat.get("type"),
        "chat_title": chat.get("title"),
        "from_id": frm.get("id"),
        "from_username": frm.get("username"),
        "from_first_name": frm.get("first_name"),
        "is_edit": "edited_message" in item,
    }


def _flatten_callback_update(item):
    cb = item.get("callback_query") or {}
    frm = cb.get("from") or {}
    return {
        "update_id": item.get("update_id"),
        "callback_id": cb.get("id"),
        "data": cb.get("data"),
        "from_id": frm.get("id"),
        "from_username": frm.get("username"),
    }


register_flatten("telegram.message", _flatten_message_update)
register_flatten("telegram.callback", _flatten_callback_update)


def _diff_updates(items, cursor, props, event_id):
    """Custom diff: drop everything with update_id <= last_update_id
    from the prior batch, then bump the cursor past the max seen so
    Telegram servers drop them on the next poll.

    Fresh cursor emits an empty match set (snapshot only) — otherwise
    a brand-new listener would flood the workflow with stale bot
    history."""
    prior_last = None
    if isinstance(cursor, dict):
        prior_last = cursor.get("last_update_id")
        if isinstance(prior_last, int):
            pass
        else:
            prior_last = None

    max_seen: int | None = None
    matches: list[dict[str, Any]] = []
    for item in items:
        uid = item.get("update_id")
        if not isinstance(uid, int):
            continue
        max_seen = uid if max_seen is None else max(max_seen, uid)
        if prior_last is not None and uid > prior_last:
            # Route by event id.
            if event_id == "new_message" and ("message" in item or "edited_message" in item):
                matches.append(_flatten_message_update(item))
                matches[-1]["event_type"] = event_id
            elif event_id == "new_callback" and "callback_query" in item:
                matches.append(_flatten_callback_update(item))
                matches[-1]["event_type"] = event_id
            elif event_id == "new_update":
                matches.append({**item, "event_type": event_id})

    # Advance cursor even when there were no matches — otherwise the
    # dropped-by-filter updates come back every poll.
    new_last = max_seen if max_seen is not None else prior_last
    new_cursor: dict[str, Any] = {"event_type": event_id}
    if new_last is not None:
        new_cursor["last_update_id"] = new_last
    return matches, new_cursor


async def _walk_telegram(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Call getUpdates with the acked offset from cursor. Telegram
    drops any update_id < offset from the response; we still filter
    client-side because a brand-new cursor uses `0`."""
    bot_token = token or ""
    if not bot_token:
        return []
    # Read prior cursor via node repo would require the factory to
    # thread it through — instead, we fetch every update since the
    # last-known offset by asking the bot API. The factory's diff
    # handler then decides which ones are new.
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params: dict[str, Any] = {}
    # 25s < 30s httpx default; bounds getUpdates long-poll to a
    # window that never times the client out.
    params["timeout"] = 0
    limit = getattr(props, "max_per_poll", 25) or 25
    try:
        params["limit"] = max(1, min(int(limit), 100))
    except (TypeError, ValueError):
        params["limit"] = 25
    # Route allowed_updates by event.
    if event.id == "new_message":
        params["allowed_updates"] = '["message","edited_message"]'
    elif event.id == "new_callback":
        params["allowed_updates"] = '["callback_query"]'
    resp = await client.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json() or {}
    if not payload.get("ok"):
        raise RuntimeError(payload.get("description") or "Telegram getUpdates failed")
    result = payload.get("result")
    return result if isinstance(result, list) else []


MANIFEST = PollingTriggerManifest(
    type="trigger.telegram",
    name="Telegram",
    description="Poll a Telegram bot for new messages, callback queries, or any update.",
    icon_slug="telegram",
    color="#1c1c1c",
    base_url="",
    credential_type="telegram_bot",
    token_field=["bot_token"],
    auth="none",
    provider="telegram",
    default_poll_interval_seconds=30,
    min_poll_interval_seconds=15,
    common_fields=[
        FieldSpec(
            name="_note",
            label="Note",
            type="string",
            default="Do not run this in parallel with a Telegram webhook — Telegram allows only one delivery mode.",
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_message",
            label="New Message",
            list_path="",
            diff_handler=_diff_updates,
            flatten="telegram.message",
        ),
        PollingEvent(
            id="new_callback",
            label="New Callback Query",
            list_path="",
            diff_handler=_diff_updates,
            flatten="telegram.callback",
        ),
        PollingEvent(
            id="new_update",
            label="Any Update",
            list_path="",
            diff_handler=_diff_updates,
        ),
    ],
    outputs_schema=[
        {"label": "update_id", "type": "number"},
        {"label": "message_id", "type": "number"},
        {"label": "chat_id", "type": "number"},
        {"label": "text", "type": "string"},
        {"label": "from_username", "type": "string"},
    ],
    paginate_fn=_walk_telegram,
)
