"""GitLab remote-picker handlers — projects, branches."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "gitlab"


def _base(cred: dict[str, Any]) -> str:
    return str(cred.get("base_url") or cred.get("host") or "https://gitlab.com").rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("GitLab credential missing access_token / api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _projects(client, cred, _params, cursor, q):  # noqa: ANN001
    page = int(cursor) if cursor and cursor.isdigit() else 1
    r = await client.get(
        f"{_base(cred)}/api/v4/projects",
        headers=_headers(cred),
        params={
            "membership": "true",
            "per_page": 50,
            "page": page,
            **({"search": q} if q else {}),
            "order_by": "last_activity_at",
        },
    )
    r.raise_for_status()
    total_pages = int(r.headers.get("X-Total-Pages", "1"))
    items = [
        LookupItem(
            id=str(p["id"]),
            label=p.get("path_with_namespace") or p.get("name") or str(p["id"]),
            sublabel=p.get("description"),
        )
        for p in r.json()
    ]
    next_cursor = str(page + 1) if page < total_pages else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _branches(client, cred, params, _cursor, q):  # noqa: ANN001
    project = (params.get("project_id") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_base(cred)}/api/v4/projects/{project}/repository/branches",
        headers=_headers(cred),
        params={"per_page": 100, **({"search": q} if q else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=b["name"], label=b["name"], sublabel="protected" if b.get("protected") else None
        )
        for b in r.json()
    ]
    return LookupResponse(items=items)


LOOKUPS = {"projects": _projects, "branches": _branches}
