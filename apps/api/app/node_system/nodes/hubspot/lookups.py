"""HubSpot remote-picker handlers — pipelines, deal stages, owners, lists."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "hubspot"

_API = "https://api.hubapi.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("HubSpot credential missing access_token / api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _pipelines(client, cred, params, _cursor, q):  # noqa: ANN001
    object_type = (params.get("object_type") or "deals").strip()
    r = await client.get(f"{_API}/crm/v3/pipelines/{object_type}", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=p["id"], label=p.get("label") or p["id"]) for p in r.json().get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _pipeline_stages(client, cred, params, _cursor, q):  # noqa: ANN001
    object_type = (params.get("object_type") or "deals").strip()
    pipeline_id = (params.get("pipeline_id") or "").strip()
    if not pipeline_id:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_API}/crm/v3/pipelines/{object_type}/{pipeline_id}/stages",
        headers=_headers(cred),
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=s["id"],
            label=s.get("label") or s["id"],
            sublabel=str(s.get("displayOrder", "")),
        )
        for s in r.json().get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _owners(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/crm/v3/owners",
        headers=_headers(cred),
        params={"limit": 100, **({"after": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=str(o["id"]),
            label=f"{o.get('firstName', '')} {o.get('lastName', '')}".strip()
            or o.get("email")
            or str(o["id"]),
            sublabel=o.get("email"),
        )
        for o in payload.get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    next_cursor = (payload.get("paging", {}).get("next") or {}).get("after")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {
    "pipelines": _pipelines,
    "pipeline_stages": _pipeline_stages,
    "owners": _owners,
}
