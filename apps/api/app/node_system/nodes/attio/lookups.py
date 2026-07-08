"""Attio remote-picker handlers — workspaces, objects, lists."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "attio"

_API = "https://api.attio.com/v2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Attio credential missing access_token / api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _objects(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/objects", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(
            id=o["api_slug"],
            label=(o.get("singular_noun") or o["api_slug"]).title(),
            sublabel=o["api_slug"],
        )
        for o in r.json().get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _lists(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/lists", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(
            id=lst["api_slug"],
            label=lst.get("name") or lst["api_slug"],
            sublabel=lst.get("parent_object"),
        )
        for lst in r.json().get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"objects": _objects, "lists": _lists}
