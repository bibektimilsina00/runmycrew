"""Instantly.ai remote-picker handlers — campaigns, lead lists."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "instantly"

_API = "https://api.instantly.ai/api/v2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Instantly credential missing api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _campaigns(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/campaigns",
        headers=_headers(cred),
        params={"limit": 100, **({"starting_after": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=c["id"], label=c.get("name") or c["id"], sublabel=c.get("status"))
        for c in payload.get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("next_starting_after")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _lead_lists(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/lead-lists", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=lst["id"], label=lst.get("name") or lst["id"])
        for lst in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"campaigns": _campaigns, "lead_lists": _lead_lists}
