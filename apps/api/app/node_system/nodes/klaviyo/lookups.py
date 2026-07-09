"""Klaviyo remote-picker handlers — lists, segments."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "klaviyo"

_API = "https://a.klaviyo.com/api"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Klaviyo credential missing api_key.")
    return {
        "Authorization": f"Klaviyo-API-Key {token}",
        "Accept": "application/vnd.api+json",
        "revision": "2024-10-15",
    }


async def _lists(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/lists",
        headers=_headers(cred),
        params={"page[size]": 100, **({"page[cursor]": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=item["id"],
            label=(item.get("attributes") or {}).get("name") or item["id"],
        )
        for item in payload.get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _segments(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/segments", headers=_headers(cred), params={"page[size]": 100})
    r.raise_for_status()
    items = [
        LookupItem(
            id=item["id"],
            label=(item.get("attributes") or {}).get("name") or item["id"],
        )
        for item in r.json().get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"lists": _lists, "segments": _segments}
