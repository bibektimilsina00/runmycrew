"""MailerLite remote-picker handlers — groups, segments, campaigns."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "mailerlite"

_API = "https://connect.mailerlite.com/api"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("MailerLite credential missing api_key.")
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


async def _groups(client, cred, _params, cursor, q):  # noqa: ANN001
    page = int(cursor) if cursor and cursor.isdigit() else 1
    r = await client.get(
        f"{_API}/groups",
        headers=_headers(cred),
        params={"limit": 100, "page": page},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=str(g["id"]), label=g.get("name") or str(g["id"]))
        for g in payload.get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    meta = payload.get("meta") or {}
    next_cursor = str(page + 1) if page < (meta.get("last_page") or 1) else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _segments(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/segments", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(s["id"]), label=s.get("name") or str(s["id"]))
        for s in r.json().get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _campaigns(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/campaigns", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(c["id"]), label=c.get("name") or str(c["id"]), sublabel=c.get("status"))
        for c in r.json().get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"groups": _groups, "segments": _segments, "campaigns": _campaigns}
