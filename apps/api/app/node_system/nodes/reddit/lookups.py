"""Reddit remote-picker handlers — subscribed subreddits."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "reddit"

_API = "https://oauth.reddit.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Reddit credential missing access_token.")
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": cred.get("user_agent") or "fuse:remote-picker:1.0",
    }


async def _subreddits(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/subreddits/mine/subscriber",
        headers=_headers(cred),
        params={"limit": 100, **({"after": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json().get("data", {})
    items = [
        LookupItem(
            id=c["data"]["display_name"],
            label=c["data"].get("display_name_prefixed") or c["data"]["display_name"],
            sublabel=c["data"].get("subscribers") and f"{c['data']['subscribers']} subs",
        )
        for c in payload.get("children", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("after")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"subreddits": _subreddits}
