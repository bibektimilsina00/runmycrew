"""Pinecone remote-picker handlers — indexes."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "pinecone"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Pinecone credential missing api_key.")
    return {"Api-Key": token, "Accept": "application/json"}


async def _indexes(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get("https://api.pinecone.io/indexes", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=i["name"], label=i["name"], sublabel=i.get("status", {}).get("state"))
        for i in r.json().get("indexes", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"indexes": _indexes}
