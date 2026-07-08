"""Dropbox remote-picker handlers — folders."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "dropbox"

_API = "https://api.dropboxapi.com/2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Dropbox credential missing access_token.")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def _folders(client, cred, params, cursor, q):  # noqa: ANN001
    parent = (params.get("parent_path") or "").strip()
    if cursor:
        r = await client.post(
            f"{_API}/files/list_folder/continue",
            headers=_headers(cred),
            json={"cursor": cursor},
        )
    else:
        r = await client.post(
            f"{_API}/files/list_folder",
            headers=_headers(cred),
            json={"path": parent, "limit": 100, "recursive": False},
        )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=e["path_lower"],
            label=e["name"],
            sublabel=e.get("path_display"),
        )
        for e in payload.get("entries", [])
        if e.get(".tag") == "folder"
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("cursor") if payload.get("has_more") else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"folders": _folders}
