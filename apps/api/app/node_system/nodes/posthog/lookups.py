"""PostHog remote-picker handlers — projects + insights + feature flags."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "posthog"


def _base(cred: dict[str, Any]) -> str:
    return str(cred.get("base_url") or cred.get("host") or "https://us.posthog.com").rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("personal_api_key") or cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("PostHog credential missing personal_api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _projects(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/api/projects/", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(p["id"]), label=p.get("name") or str(p["id"]))
        for p in r.json().get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _feature_flags(client, cred, params, _cursor, q):  # noqa: ANN001
    project = (params.get("project_id") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_base(cred)}/api/projects/{project}/feature_flags/",
        headers=_headers(cred),
    )
    r.raise_for_status()
    items = [
        LookupItem(id=f["key"], label=f.get("name") or f["key"], sublabel=f["key"])
        for f in r.json().get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _insights(client, cred, params, _cursor, q):  # noqa: ANN001
    project = (params.get("project_id") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_base(cred)}/api/projects/{project}/insights/",
        headers=_headers(cred),
    )
    r.raise_for_status()
    items = [
        LookupItem(id=str(i["id"]), label=i.get("name") or str(i["id"]))
        for i in r.json().get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"projects": _projects, "feature_flags": _feature_flags, "insights": _insights}
