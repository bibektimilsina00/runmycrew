"""Jira remote-picker handlers — projects + issue types.

Jira's cloud REST API sits under `<site>/rest/api/3`. The site host
lives on the credential (`site_url` from an OAuth cred or `base_url`
from an API key cred). Basic auth uses email + api_key; OAuth uses
bearer token.
"""

from __future__ import annotations

from base64 import b64encode
from typing import Any

import httpx

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "jira"


def _base(cred: dict[str, Any]) -> str:
    base = cred.get("site_url") or cred.get("base_url") or cred.get("host")
    if not base:
        raise ValueError("Jira credential is missing a site URL.")
    return str(base).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    if token := cred.get("access_token"):
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    email = cred.get("email") or cred.get("user")
    api_key = cred.get("api_key") or cred.get("api_token")
    if email and api_key:
        creds = b64encode(f"{email}:{api_key}".encode()).decode()
        return {"Authorization": f"Basic {creds}", "Accept": "application/json"}
    raise ValueError("Jira credential missing access_token or (email, api_key) pair.")


async def _projects(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    _params: dict[str, str],
    cursor: str | None,
    q: str | None,
) -> LookupResponse:
    start_at = int(cursor) if cursor and cursor.isdigit() else 0
    params: dict[str, Any] = {"startAt": start_at, "maxResults": 50}
    if q:
        params["query"] = q
    r = await client.get(
        f"{_base(cred)}/rest/api/3/project/search",
        headers=_headers(cred),
        params=params,
    )
    r.raise_for_status()
    payload = r.json()
    values = payload.get("values", [])
    items = [
        LookupItem(
            id=p["key"],
            label=p["name"],
            sublabel=p["key"],
        )
        for p in values
    ]
    is_last = bool(payload.get("isLast", True))
    next_cursor = None if is_last else str(start_at + len(values))
    return LookupResponse(items=items, cursor=next_cursor, has_more=not is_last)


async def _issue_types(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    params: dict[str, str],
    _cursor: str | None,
    q: str | None,
) -> LookupResponse:
    """Issue types either scoped to a project (`?project=PROJKEY`) or
    global across the site."""
    project = (params.get("project") or params.get("project_id") or "").strip()
    if project:
        path = f"{_base(cred)}/rest/api/3/issue/createmeta/{project}/issuetypes"
    else:
        path = f"{_base(cred)}/rest/api/3/issuetype"
    r = await client.get(path, headers=_headers(cred))
    r.raise_for_status()
    payload = r.json()
    # createmeta returns { values: [...] }; global returns a bare list.
    raw = payload.get("values") if isinstance(payload, dict) else payload
    items = [
        LookupItem(id=t["id"], label=t["name"], sublabel=t.get("description")) for t in (raw or [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {
    "projects": _projects,
    "issue_types": _issue_types,
}
