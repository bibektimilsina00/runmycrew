"""Lemlist remote-picker handlers — campaigns."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "lemlist"

_API = "https://api.lemlist.com/api"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    key = cred.get("api_key")
    if not key:
        raise ValueError("Lemlist credential missing api_key.")
    return {"Authorization": "Basic " + b64encode(f":{key}".encode()).decode()}


async def _campaigns(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/campaigns", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=c["_id"], label=c.get("name") or c["_id"], sublabel=c.get("status"))
        for c in r.json()
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"campaigns": _campaigns}
