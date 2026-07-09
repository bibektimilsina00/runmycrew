"""Spotify remote-picker handlers — playlists, artists, albums."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "spotify"

_API = "https://api.spotify.com/v1"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Spotify credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _playlists(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/me/playlists",
        headers=_headers(cred),
        params={"limit": 50, **({"offset": cursor} if cursor and cursor.isdigit() else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=p["id"], label=p.get("name") or p["id"], sublabel=p.get("description"))
        for p in payload.get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    total = payload.get("total", 0)
    next_offset = int(payload.get("offset") or 0) + int(payload.get("limit") or 0)
    next_cursor = str(next_offset) if next_offset < total else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _search(client, cred, kind, q):
    if not q:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_API}/search",
        headers=_headers(cred),
        params={"q": q, "type": kind, "limit": 50},
    )
    r.raise_for_status()
    section = r.json().get(kind + "s") or {}
    items = [
        LookupItem(id=item["id"], label=item.get("name") or item["id"])
        for item in section.get("items", [])
    ]
    return LookupResponse(items=items)


async def _artists(client, cred, _params, _cursor, q):  # noqa: ANN001
    return await _search(client, cred, "artist", q)


async def _albums(client, cred, _params, _cursor, q):  # noqa: ANN001
    return await _search(client, cred, "album", q)


LOOKUPS = {"playlists": _playlists, "artists": _artists, "albums": _albums}
