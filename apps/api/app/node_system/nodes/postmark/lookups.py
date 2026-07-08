"""Postmark remote-picker handlers — servers, templates."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "postmark"

_API = "https://api.postmarkapp.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    # Account-level endpoints use `X-Postmark-Account-Token`, server-level
    # use `X-Postmark-Server-Token`. Prefer account when supplied.
    if account := cred.get("account_token"):
        return {"X-Postmark-Account-Token": account, "Accept": "application/json"}
    server = cred.get("server_token") or cred.get("api_key")
    if not server:
        raise ValueError("Postmark credential missing account_token or server_token.")
    return {"X-Postmark-Server-Token": server, "Accept": "application/json"}


async def _servers(client, cred, _params, cursor, q):  # noqa: ANN001
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_API}/servers",
        headers=_headers(cred),
        params={"count": 100, "offset": offset, **({"name": q} if q else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=str(s["ID"]), label=s.get("Name") or str(s["ID"]), sublabel=s.get("Color"))
        for s in payload.get("Servers", [])
    ]
    total = payload.get("TotalCount", 0)
    next_cursor = str(offset + 100) if offset + 100 < total else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _templates(client, cred, _params, cursor, q):  # noqa: ANN001
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_API}/templates",
        headers=_headers(cred),
        params={"count": 100, "offset": offset},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=str(t["TemplateId"]),
            label=t.get("Name") or str(t["TemplateId"]),
            sublabel=t.get("Alias"),
        )
        for t in payload.get("Templates", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    total = payload.get("TotalCount", 0)
    next_cursor = str(offset + 100) if offset + 100 < total else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"servers": _servers, "templates": _templates}
