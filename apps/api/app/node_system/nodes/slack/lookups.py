"""Slack remote-picker handlers — channels + users.

Slack pages via `cursor` (opaque string). We map that straight through
to `LookupResponse.cursor` so the frontend's infinite scroll keeps
working with no per-provider knowledge.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "slack"

_API = "https://slack.com/api"
_PER_PAGE = 100


def _auth_headers(cred: dict[str, Any]) -> dict[str, str]:
    # Slack OAuth stores the bot token under `access_token`; the API
    # key flow uses `api_key`. Accept both so the same handler powers
    # both credential types.
    token = cred.get("access_token") or cred.get("api_key") or cred.get("bot_token")
    if not token:
        raise ValueError("Slack credential is missing a bot token.")
    return {"Authorization": f"Bearer {token}"}


async def _channels(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    _params: dict[str, str],
    cursor: str | None,
    q: str | None,
) -> LookupResponse:
    """List public + private channels the token can see."""
    r = await client.get(
        f"{_API}/conversations.list",
        headers=_auth_headers(cred),
        params={
            "types": "public_channel,private_channel",
            "exclude_archived": "true",
            "limit": _PER_PAGE,
            **({"cursor": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Slack channels lookup failed: {payload.get('error')}")

    items = [
        LookupItem(
            id=c["id"],
            label=f"#{c['name']}",
            sublabel=("Private" if c.get("is_private") else None),
        )
        for c in payload.get("channels", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]

    next_cursor = (payload.get("response_metadata") or {}).get("next_cursor") or None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _users(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    _params: dict[str, str],
    cursor: str | None,
    q: str | None,
) -> LookupResponse:
    """List workspace members (real users, no bots)."""
    r = await client.get(
        f"{_API}/users.list",
        headers=_auth_headers(cred),
        params={
            "limit": _PER_PAGE,
            **({"cursor": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Slack users lookup failed: {payload.get('error')}")

    items = [
        LookupItem(
            id=u["id"],
            label=u.get("real_name") or u.get("name") or u["id"],
            sublabel=u.get("profile", {}).get("email") or u.get("name"),
        )
        for u in payload.get("members", [])
        if not u.get("is_bot") and not u.get("deleted")
    ]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]

    next_cursor = (payload.get("response_metadata") or {}).get("next_cursor") or None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {
    "channels": _channels,
    "users": _users,
}
