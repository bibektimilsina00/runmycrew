"""Azure DevOps remote-picker handlers — projects, repositories, pipelines."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "azure_devops"


def _base(cred: dict[str, Any]) -> str:
    org = cred.get("organization") or cred.get("org_name") or cred.get("base_url")
    if not org:
        raise ValueError("Azure DevOps credential missing organization.")
    org = str(org).rstrip("/")
    if not org.startswith("http"):
        org = f"https://dev.azure.com/{org}"
    return org


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    pat = cred.get("api_key") or cred.get("access_token") or cred.get("personal_access_token")
    if not pat:
        raise ValueError("Azure DevOps credential missing PAT.")
    return {
        "Authorization": "Basic " + b64encode(f":{pat}".encode()).decode(),
        "Accept": "application/json",
    }


async def _projects(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/_apis/projects",
        headers=_headers(cred),
        params={"api-version": "7.1"},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=p["id"], label=p.get("name") or p["id"], sublabel=p.get("state"))
        for p in r.json().get("value", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _repositories(client, cred, params, _cursor, q):  # noqa: ANN001
    project = (params.get("project") or params.get("project_id") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_base(cred)}/{project}/_apis/git/repositories",
        headers=_headers(cred),
        params={"api-version": "7.1"},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=repo["id"], label=repo.get("name") or repo["id"], sublabel=repo.get("defaultBranch")
        )
        for repo in r.json().get("value", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _pipelines(client, cred, params, _cursor, q):  # noqa: ANN001
    project = (params.get("project") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_base(cred)}/{project}/_apis/pipelines",
        headers=_headers(cred),
        params={"api-version": "7.1"},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=str(p["id"]), label=p.get("name") or str(p["id"]), sublabel=p.get("folder"))
        for p in r.json().get("value", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"projects": _projects, "repositories": _repositories, "pipelines": _pipelines}
