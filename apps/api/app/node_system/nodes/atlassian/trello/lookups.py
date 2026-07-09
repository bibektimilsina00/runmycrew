"""Trello remote-picker handlers — boards, lists."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "trello"


def _auth(cred: dict[str, Any]) -> dict[str, str]:
    key = cred.get("app_key") or cred.get("api_key")
    token = cred.get("token") or cred.get("access_token")
    if not key or not token:
        raise ValueError("Trello credential missing app_key + token.")
    return {"key": key, "token": token}


async def _boards(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://api.trello.com/1/members/me/boards",
        params={**_auth(cred), "fields": "name,url,closed"},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=b["id"], label=b.get("name") or b["id"], sublabel=b.get("url"))
        for b in r.json()
        if not b.get("closed")
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _lists(client, cred, params, _cursor, q):  # noqa: ANN001
    board = (params.get("board_id") or params.get("board") or "").strip()
    if not board:
        return LookupResponse(items=[])
    r = await client.get(
        f"https://api.trello.com/1/boards/{board}/lists",
        params={**_auth(cred), "fields": "name,closed"},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=lst["id"], label=lst.get("name") or lst["id"])
        for lst in r.json()
        if not lst.get("closed")
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"boards": _boards, "lists": _lists}
