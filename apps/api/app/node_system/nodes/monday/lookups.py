"""Monday.com remote-picker handlers — boards, columns."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "monday"

_API = "https://api.monday.com/v2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Monday credential missing api_key.")
    return {"Authorization": token, "Content-Type": "application/json"}


async def _gql(client, cred, query, variables=None):
    r = await client.post(
        _API, headers=_headers(cred), json={"query": query, "variables": variables or {}}
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError(f"Monday GraphQL: {payload['errors']}")
    return payload.get("data") or {}


async def _boards(client, cred, _params, _cursor, q):  # noqa: ANN001
    data = await _gql(client, cred, "{ boards(limit: 100) { id name state description } }")
    items = [
        LookupItem(
            id=str(b["id"]),
            label=b.get("name") or str(b["id"]),
            sublabel=b.get("state"),
        )
        for b in data.get("boards", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _columns(client, cred, params, _cursor, q):  # noqa: ANN001
    board = (params.get("board_id") or "").strip()
    if not board:
        return LookupResponse(items=[])
    data = await _gql(
        client,
        cred,
        "query($ids:[ID!]) { boards(ids:$ids) { columns { id title type } } }",
        {"ids": [board]},
    )
    boards = data.get("boards") or []
    if not boards:
        return LookupResponse(items=[])
    items = [
        LookupItem(id=c["id"], label=c.get("title") or c["id"], sublabel=c.get("type"))
        for c in (boards[0].get("columns") or [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"boards": _boards, "columns": _columns}
