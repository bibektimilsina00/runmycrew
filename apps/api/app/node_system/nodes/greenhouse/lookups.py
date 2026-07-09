"""Greenhouse remote-picker handlers — jobs, users, offices, departments."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "greenhouse"

_API = "https://harvest.greenhouse.io/v1"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    key = cred.get("api_key") or cred.get("access_token")
    if not key:
        raise ValueError("Greenhouse credential missing api_key.")
    return {"Authorization": "Basic " + b64encode(f"{key}:".encode()).decode()}


async def _jobs(client, cred, _params, cursor, q):  # noqa: ANN001
    page = int(cursor) if cursor and cursor.isdigit() else 1
    r = await client.get(
        f"{_API}/jobs",
        headers=_headers(cred),
        params={"per_page": 100, "page": page},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=str(j["id"]), label=j.get("name") or str(j["id"]), sublabel=j.get("status"))
        for j in r.json()
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = str(page + 1) if len(items) >= 100 else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _users(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/users", headers=_headers(cred), params={"per_page": 500})
    r.raise_for_status()
    items = [
        LookupItem(
            id=str(u["id"]),
            label=u.get("name") or str(u["id"]),
            sublabel=u.get("primary_email_address"),
        )
        for u in r.json()
    ]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    return LookupResponse(items=items)


async def _offices(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/offices", headers=_headers(cred), params={"per_page": 100})
    r.raise_for_status()
    items = [LookupItem(id=str(o["id"]), label=o.get("name") or str(o["id"])) for o in r.json()]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _departments(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/departments", headers=_headers(cred), params={"per_page": 100})
    r.raise_for_status()
    items = [LookupItem(id=str(d["id"]), label=d.get("name") or str(d["id"])) for d in r.json()]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"jobs": _jobs, "users": _users, "offices": _offices, "departments": _departments}
