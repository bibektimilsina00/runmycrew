"""Confluence remote-picker handlers — spaces, pages."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "confluence"


def _base(cred: dict[str, Any]) -> str:
    base = cred.get("site_url") or cred.get("base_url") or cred.get("host")
    if not base:
        raise ValueError("Confluence credential is missing a site URL.")
    return str(base).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    if token := cred.get("access_token"):
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    email = cred.get("email") or cred.get("user")
    api_key = cred.get("api_key") or cred.get("api_token")
    if email and api_key:
        creds = b64encode(f"{email}:{api_key}".encode()).decode()
        return {"Authorization": f"Basic {creds}", "Accept": "application/json"}
    raise ValueError("Confluence credential missing access_token or (email, api_key).")


async def _spaces(client, cred, _params, cursor, q):  # noqa: ANN001
    start = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_base(cred)}/wiki/rest/api/space",
        headers=_headers(cred),
        params={"start": start, "limit": 50},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=s["key"], label=s.get("name") or s["key"], sublabel=s["key"])
        for s in payload.get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    size = payload.get("size", 0)
    next_cursor = str(start + size) if size >= 50 else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _pages(client, cred, params, cursor, q):  # noqa: ANN001
    space = (params.get("space") or params.get("space_key") or "").strip()
    if not space:
        return LookupResponse(items=[])
    start = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_base(cred)}/wiki/rest/api/space/{space}/content/page",
        headers=_headers(cred),
        params={"start": start, "limit": 50},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=p["id"], label=p.get("title") or p["id"]) for p in payload.get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    size = payload.get("size", 0)
    next_cursor = str(start + size) if size >= 50 else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"spaces": _spaces, "pages": _pages}
