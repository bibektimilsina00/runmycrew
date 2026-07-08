"""Microsoft brand-level remote-picker handlers.

Every Microsoft service (Outlook, OneDrive, Teams, SharePoint,
Planner, Excel, Dataverse, Azure AD) reads the same OAuth token via
Microsoft Graph, so all handlers live at the brand root.

Graph is versioned by URL segment (`/v1.0/…`). Endpoints paginate via
`@odata.nextLink` — we crop it to the raw cursor token so subsequent
calls can re-send it.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "microsoft"

_GRAPH = "https://graph.microsoft.com/v1.0"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Microsoft credential is missing access_token.")
    return {"Authorization": f"Bearer {token}"}


def _extract_skiptoken(next_link: str | None) -> str | None:
    if not next_link:
        return None
    # Graph's next-link carries an opaque `$skiptoken=…` — round-trip
    # by echoing it back on the follow-up request.
    from urllib.parse import parse_qs, urlparse

    q = parse_qs(urlparse(next_link).query)
    tok = q.get("$skiptoken") or q.get("skiptoken")
    return tok[0] if tok else None


async def _outlook_folders(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_GRAPH}/me/mailFolders",
        headers=_headers(cred),
        params={"$top": 100, **({"$skiptoken": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=f["id"], label=f.get("displayName") or f["id"])
        for f in payload.get("value", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = _extract_skiptoken(payload.get("@odata.nextLink"))
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _onedrive_folders(client, cred, params, cursor, q):  # noqa: ANN001
    parent = (params.get("parent_id") or "root").strip() or "root"
    path = (
        f"{_GRAPH}/me/drive/items/{parent}/children"
        if parent != "root"
        else f"{_GRAPH}/me/drive/root/children"
    )
    r = await client.get(
        path,
        headers=_headers(cred),
        params={
            "$top": 100,
            "$filter": "folder ne null",
            **({"$skiptoken": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=f["id"], label=f.get("name") or f["id"])
        for f in payload.get("value", [])
        if f.get("folder") is not None
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = _extract_skiptoken(payload.get("@odata.nextLink"))
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _teams(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_GRAPH}/me/joinedTeams",
        headers=_headers(cred),
        params={"$top": 100, **({"$skiptoken": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=t["id"],
            label=t.get("displayName") or t["id"],
            sublabel=t.get("description"),
        )
        for t in payload.get("value", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = _extract_skiptoken(payload.get("@odata.nextLink"))
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _channels(client, cred, params, _cursor, q):  # noqa: ANN001
    team_id = (params.get("team_id") or params.get("team") or "").strip()
    if not team_id:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_GRAPH}/teams/{team_id}/channels",
        headers=_headers(cred),
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=c["id"], label=c.get("displayName") or c["id"], sublabel=c.get("membershipType")
        )
        for c in r.json().get("value", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _sharepoint_sites(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_GRAPH}/sites",
        headers=_headers(cred),
        params={
            "search": q or "*",
            **({"$skiptoken": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=s["id"],
            label=s.get("displayName") or s.get("name") or s["id"],
            sublabel=s.get("webUrl"),
        )
        for s in payload.get("value", [])
    ]
    next_cursor = _extract_skiptoken(payload.get("@odata.nextLink"))
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _planner_plans(client, cred, params, _cursor, q):  # noqa: ANN001
    group_id = (params.get("group_id") or params.get("team_id") or "").strip()
    if not group_id:
        # Fall back to the current user's plans.
        r = await client.get(f"{_GRAPH}/me/planner/plans", headers=_headers(cred))
    else:
        r = await client.get(f"{_GRAPH}/groups/{group_id}/planner/plans", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=p["id"], label=p.get("title") or p["id"]) for p in r.json().get("value", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _excel_workbooks(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_GRAPH}/me/drive/root/search(q='xlsx')",
        headers=_headers(cred),
        params={"$top": 100, **({"$skiptoken": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=f["id"], label=f.get("name") or f["id"], sublabel=f.get("webUrl"))
        for f in payload.get("value", [])
        if (f.get("name") or "").lower().endswith(".xlsx")
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = _extract_skiptoken(payload.get("@odata.nextLink"))
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {
    "outlook_folders": _outlook_folders,
    "onedrive_folders": _onedrive_folders,
    "teams": _teams,
    "channels": _channels,
    "sharepoint_sites": _sharepoint_sites,
    "planner_plans": _planner_plans,
    "excel_workbooks": _excel_workbooks,
}
