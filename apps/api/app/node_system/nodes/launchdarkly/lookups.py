"""LaunchDarkly remote-picker handlers — projects, environments, flags."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "launchdarkly"

_API = "https://app.launchdarkly.com/api/v2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("LaunchDarkly credential missing api_key.")
    return {"Authorization": token}


async def _projects(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/projects", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=p["key"], label=p.get("name") or p["key"], sublabel=p["key"])
        for p in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _environments(client, cred, params, _cursor, q):  # noqa: ANN001
    project = (params.get("project_key") or params.get("project") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(f"{_API}/projects/{project}/environments", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=e["key"], label=e.get("name") or e["key"], sublabel=e.get("color"))
        for e in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _flags(client, cred, params, _cursor, q):  # noqa: ANN001
    project = (params.get("project_key") or params.get("project") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_API}/flags/{project}",
        headers=_headers(cred),
        params={"limit": 100},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=f["key"], label=f.get("name") or f["key"], sublabel=f["key"])
        for f in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"projects": _projects, "environments": _environments, "flags": _flags}
