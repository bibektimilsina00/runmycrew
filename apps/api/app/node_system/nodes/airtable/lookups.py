"""Airtable remote-picker handlers — bases + tables."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "airtable"

_API = "https://api.airtable.com/v0"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Airtable credential missing api_key / access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _bases(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/meta/bases",
        headers=_headers(cred),
        params={**({"offset": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=b["id"],
            label=b.get("name") or b["id"],
            sublabel=b.get("permissionLevel"),
        )
        for b in payload.get("bases", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(
        items=items, cursor=payload.get("offset"), has_more=bool(payload.get("offset"))
    )


async def _tables(client, cred, params, _cursor, q):  # noqa: ANN001
    base_id = (params.get("base_id") or params.get("base") or "").strip()
    if not base_id:
        return LookupResponse(items=[])
    r = await client.get(f"{_API}/meta/bases/{base_id}/tables", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(
            id=t["id"],
            label=t.get("name") or t["id"],
            sublabel=t.get("primaryFieldId"),
        )
        for t in r.json().get("tables", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {
    "bases": _bases,
    "tables": _tables,
}
