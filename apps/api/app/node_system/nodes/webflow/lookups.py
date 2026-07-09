"""Webflow remote-picker handlers — sites, collections."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "webflow"

_API = "https://api.webflow.com/v2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Webflow credential missing access_token.")
    return {"Authorization": f"Bearer {token}", "accept-version": "1.0.0"}


async def _sites(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/sites", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=s["id"], label=s.get("displayName") or s["id"], sublabel=s.get("shortName"))
        for s in r.json().get("sites", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _collections(client, cred, params, _cursor, q):  # noqa: ANN001
    site = (params.get("site_id") or "").strip()
    if not site:
        return LookupResponse(items=[])
    r = await client.get(f"{_API}/sites/{site}/collections", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=c["id"], label=c.get("displayName") or c["id"], sublabel=c.get("slug"))
        for c in r.json().get("collections", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"sites": _sites, "collections": _collections}
