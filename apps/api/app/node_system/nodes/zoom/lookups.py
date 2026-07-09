"""Zoom remote-picker handlers — users, meetings."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "zoom"

_API = "https://api.zoom.us/v2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Zoom credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _users(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/users",
        headers=_headers(cred),
        params={"page_size": 100, **({"next_page_token": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=u["id"],
            label=f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()
            or u.get("email")
            or u["id"],
            sublabel=u.get("email"),
        )
        for u in payload.get("users", [])
    ]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    next_cursor = payload.get("next_page_token") or None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _meetings(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/users/me/meetings",
        headers=_headers(cred),
        params={
            "type": "scheduled",
            "page_size": 100,
            **({"next_page_token": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=str(m["id"]), label=m.get("topic") or str(m["id"]), sublabel=m.get("start_time")
        )
        for m in payload.get("meetings", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("next_page_token") or None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"users": _users, "meetings": _meetings}
