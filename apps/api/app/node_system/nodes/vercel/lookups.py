"""Vercel remote-picker handlers — projects, teams."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "vercel"

_API = "https://api.vercel.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Vercel credential missing access_token / api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _projects(client, cred, params, _cursor, q):  # noqa: ANN001
    team_id = (params.get("team_id") or "").strip()
    r = await client.get(
        f"{_API}/v9/projects",
        headers=_headers(cred),
        params={"limit": 100, **({"teamId": team_id} if team_id else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=p["id"],
            label=p.get("name") or p["id"],
            sublabel=p.get("framework"),
        )
        for p in r.json().get("projects", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _teams(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/v2/teams", headers=_headers(cred), params={"limit": 100})
    r.raise_for_status()
    items = [
        LookupItem(id=t["id"], label=t.get("name") or t["id"], sublabel=t.get("slug"))
        for t in r.json().get("teams", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"projects": _projects, "teams": _teams}
