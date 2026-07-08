"""Box remote-picker handlers — folders."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "box"

_API = "https://api.box.com/2.0"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Box credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _folders(client, cred, params, cursor, q):  # noqa: ANN001
    parent = (params.get("parent_id") or "0").strip() or "0"
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_API}/folders/{parent}/items",
        headers=_headers(cred),
        params={"limit": 100, "offset": offset, "fields": "id,name,type"},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=e["id"], label=e.get("name") or e["id"])
        for e in payload.get("entries", [])
        if e.get("type") == "folder"
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    total = payload.get("total_count", 0)
    next_cursor = str(offset + 100) if offset + 100 < total else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"folders": _folders}
