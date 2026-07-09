"""Luma remote-picker handlers — events."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "luma"

_API = "https://api.lu.ma/public/v1"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Luma credential missing api_key.")
    return {"x-luma-api-key": token, "Accept": "application/json"}


async def _events(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/calendar/list-events",
        headers=_headers(cred),
        params={"pagination_limit": 100, **({"pagination_cursor": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = []
    for entry in payload.get("entries", []):
        ev = entry.get("event") or {}
        items.append(
            LookupItem(
                id=ev.get("api_id"),
                label=ev.get("name") or ev.get("api_id"),
                sublabel=ev.get("start_at"),
            )
        )
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("next_cursor")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"events": _events}
