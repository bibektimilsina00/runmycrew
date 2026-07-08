"""Apify remote-picker handlers — actors + datasets."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "apify"

_API = "https://api.apify.com/v2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Apify credential missing api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _actors(client, cred, _params, cursor, q):  # noqa: ANN001
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_API}/acts",
        headers=_headers(cred),
        params={"my": "true", "limit": 100, "offset": offset, "desc": "true"},
    )
    r.raise_for_status()
    payload = r.json().get("data", {})
    items = [
        LookupItem(id=a["id"], label=a.get("name") or a["id"], sublabel=a.get("username"))
        for a in payload.get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    total = payload.get("total", 0)
    next_cursor = str(offset + 100) if offset + 100 < total else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _datasets(client, cred, _params, cursor, q):  # noqa: ANN001
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_API}/datasets",
        headers=_headers(cred),
        params={"limit": 100, "offset": offset, "desc": "true"},
    )
    r.raise_for_status()
    payload = r.json().get("data", {})
    items = [
        LookupItem(id=d["id"], label=d.get("name") or d["id"]) for d in payload.get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    total = payload.get("total", 0)
    next_cursor = str(offset + 100) if offset + 100 < total else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"actors": _actors, "datasets": _datasets}
