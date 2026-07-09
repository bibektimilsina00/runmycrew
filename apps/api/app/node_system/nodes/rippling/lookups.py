"""Rippling remote-picker handlers — departments, employees."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "rippling"

_API = "https://api.rippling.com/platform/api"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Rippling credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _employees(client, cred, _params, cursor, q):  # noqa: ANN001
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_API}/employees",
        headers=_headers(cred),
        params={"limit": 100, "offset": offset},
    )
    r.raise_for_status()
    data = r.json()
    items = [
        LookupItem(
            id=str(e["id"]),
            label=f"{e.get('firstName', '')} {e.get('lastName', '')}".strip() or str(e["id"]),
            sublabel=e.get("workEmail"),
        )
        for e in (data if isinstance(data, list) else data.get("employees", []))
    ]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    next_cursor = str(offset + 100) if len(items) >= 100 else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _departments(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/departments", headers=_headers(cred))
    r.raise_for_status()
    data = r.json()
    items = [
        LookupItem(id=str(d["id"]), label=d.get("name") or str(d["id"]))
        for d in (data if isinstance(data, list) else data.get("departments", []))
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"employees": _employees, "departments": _departments}
