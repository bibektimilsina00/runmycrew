"""Hex remote-picker handlers — projects."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "hex"

_API = "https://app.hex.tech/api/v1"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Hex credential missing api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _projects(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/projects",
        headers=_headers(cred),
        params={"limit": 100, **({"after": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=p["id"], label=p.get("title") or p["id"], sublabel=p.get("status"))
        for p in payload.get("values", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = (payload.get("pagination") or {}).get("after")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"projects": _projects}
