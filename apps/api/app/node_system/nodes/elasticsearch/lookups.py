"""Elasticsearch remote-picker handlers — indices."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "elasticsearch"


def _base(cred: dict[str, Any]) -> str:
    host = cred.get("host") or cred.get("base_url") or cred.get("url")
    if not host:
        raise ValueError("Elasticsearch credential missing host.")
    return str(host).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    if token := cred.get("api_key"):
        return {"Authorization": f"ApiKey {token}"}
    user = cred.get("username") or cred.get("user")
    pw = cred.get("password")
    if user and pw:
        return {"Authorization": "Basic " + b64encode(f"{user}:{pw}".encode()).decode()}
    return {}


async def _indices(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/_cat/indices",
        headers={**_headers(cred), "Accept": "application/json"},
        params={"format": "json"},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=idx.get("index"),
            label=idx.get("index"),
            sublabel=f"{idx.get('docs.count', 0)} docs · {idx.get('store.size') or ''}".strip(),
        )
        for idx in r.json()
        if idx.get("index") and not idx["index"].startswith(".")
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"indices": _indices}
