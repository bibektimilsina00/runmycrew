"""Calendly remote-picker handlers — event types."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "calendly"

_API = "https://api.calendly.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Calendly credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _me(client, cred: dict[str, Any]) -> str:
    """Calendly requires an organization or user URI on most list calls
    — fetch the current user's URI once and reuse."""
    r = await client.get(f"{_API}/users/me", headers=_headers(cred))
    r.raise_for_status()
    return r.json()["resource"]["uri"]


async def _event_types(client, cred, _params, cursor, q):  # noqa: ANN001
    user = await _me(client, cred)
    r = await client.get(
        f"{_API}/event_types",
        headers=_headers(cred),
        params={
            "user": user,
            "count": 100,
            **({"page_token": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=e["uri"],
            label=e.get("name") or e["uri"],
            sublabel=e.get("duration") and f"{e['duration']} min",
        )
        for e in payload.get("collection", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = (payload.get("pagination") or {}).get("next_page_token")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"event_types": _event_types}
