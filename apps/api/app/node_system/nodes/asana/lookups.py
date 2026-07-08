"""Asana remote-picker handlers — workspaces, projects."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "asana"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Asana credential missing access_token / api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _workspaces(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get("https://app.asana.com/api/1.0/workspaces", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=w["gid"], label=w.get("name") or w["gid"]) for w in r.json().get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _projects(client, cred, params, cursor, q):  # noqa: ANN001
    workspace = (params.get("workspace_id") or params.get("workspace") or "").strip()
    r = await client.get(
        "https://app.asana.com/api/1.0/projects",
        headers=_headers(cred),
        params={
            "limit": 100,
            **({"workspace": workspace} if workspace else {}),
            **({"offset": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=p["gid"], label=p.get("name") or p["gid"]) for p in payload.get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = (payload.get("next_page") or {}).get("offset")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"workspaces": _workspaces, "projects": _projects}
