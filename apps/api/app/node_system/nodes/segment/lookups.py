"""Segment (Twilio Segment) remote-picker handlers — workspaces, sources."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "segment"

_API = "https://api.segmentapis.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Segment credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _workspaces(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/workspaces", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=w["id"], label=w.get("name") or w["id"], sublabel=w.get("slug"))
        for w in r.json().get("data", {}).get("workspaces", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _sources(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/sources",
        headers=_headers(cred),
        params={
            "pagination.count": 100,
            **({"pagination.cursor": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json().get("data", {})
    items = [
        LookupItem(id=s["id"], label=s.get("name") or s["id"], sublabel=s.get("slug"))
        for s in payload.get("sources", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = (payload.get("pagination") or {}).get("next")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"workspaces": _workspaces, "sources": _sources}
