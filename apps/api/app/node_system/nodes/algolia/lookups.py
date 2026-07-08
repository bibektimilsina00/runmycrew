"""Algolia remote-picker handlers — indices."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "algolia"


def _base(cred: dict[str, Any]) -> str:
    app_id = cred.get("app_id") or cred.get("application_id")
    if not app_id:
        raise ValueError("Algolia credential missing app_id.")
    return f"https://{app_id}-dsn.algolia.net"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    key = cred.get("admin_api_key") or cred.get("api_key")
    app = cred.get("app_id") or cred.get("application_id")
    if not key or not app:
        raise ValueError("Algolia credential missing app_id / api_key.")
    return {"X-Algolia-Application-Id": app, "X-Algolia-API-Key": key}


async def _indices(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/1/indexes", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=i["name"], label=i["name"], sublabel=str(i.get("entries", 0)))
        for i in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"indices": _indices}
