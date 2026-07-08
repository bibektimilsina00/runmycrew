"""Linear remote-picker handlers — teams, projects, states.

Linear is GraphQL-only. Every lookup issues a single query against
`https://api.linear.app/graphql` with the api-key header. States are
scoped to a team (`team_id`), so the states handler mirrors the
"depends on Team" pattern used by GitHub's repo picker.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "linear"

_API = "https://api.linear.app/graphql"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Linear credential is missing an api_key.")
    return {"Authorization": token, "Content-Type": "application/json"}


async def _gql(client: httpx.AsyncClient, cred: dict[str, Any], query: str) -> dict[str, Any]:
    r = await client.post(_API, headers=_headers(cred), json={"query": query})
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError(f"Linear GraphQL error: {payload['errors']}")
    return payload.get("data") or {}


async def _teams(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    _params: dict[str, str],
    _cursor: str | None,
    q: str | None,
) -> LookupResponse:
    data = await _gql(client, cred, "{ teams { nodes { id key name } } }")
    nodes = (data.get("teams") or {}).get("nodes") or []
    items = [LookupItem(id=t["id"], label=t["name"], sublabel=t.get("key")) for t in nodes]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    return LookupResponse(items=items)


async def _projects(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    _params: dict[str, str],
    _cursor: str | None,
    q: str | None,
) -> LookupResponse:
    data = await _gql(client, cred, "{ projects { nodes { id name state description } } }")
    nodes = (data.get("projects") or {}).get("nodes") or []
    items = [
        LookupItem(id=p["id"], label=p["name"], sublabel=p.get("state") or p.get("description"))
        for p in nodes
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _states(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    params: dict[str, str],
    _cursor: str | None,
    q: str | None,
) -> LookupResponse:
    """Workflow states scoped to a single team. Empty result when
    the picker is asked before Team is set."""
    team_id = (params.get("team_id") or params.get("team") or "").strip()
    if not team_id:
        return LookupResponse(items=[])
    query = (
        '{ team(id: "'
        + team_id.replace('"', '\\"')
        + '") { states { nodes { id name type color } } } }'
    )
    data = await _gql(client, cred, query)
    nodes = ((data.get("team") or {}).get("states") or {}).get("nodes") or []
    items = [LookupItem(id=s["id"], label=s["name"], sublabel=s.get("type")) for s in nodes]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {
    "teams": _teams,
    "projects": _projects,
    "states": _states,
}
