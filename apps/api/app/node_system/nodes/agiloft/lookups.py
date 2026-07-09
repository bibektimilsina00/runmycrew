"""Agiloft remote-picker handlers — tables. Uses REST v1 EUI."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "agiloft"


def _base(cred: dict[str, Any]) -> str:
    host = cred.get("base_url") or cred.get("host")
    if not host:
        raise ValueError("Agiloft credential missing base_url.")
    return str(host).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Agiloft credential missing access_token.")
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


async def _tables(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/gui2/rest/v2/tables", headers=_headers(cred))
    r.raise_for_status()
    data = r.json()
    items = []
    for row in data if isinstance(data, list) else []:
        name = row.get("name") or row.get("label") or row.get("id")
        items.append(LookupItem(id=str(row.get("id") or name), label=name))
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"tables": _tables}
