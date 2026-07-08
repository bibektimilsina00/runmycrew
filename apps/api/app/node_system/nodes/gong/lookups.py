"""Gong remote-picker handlers — users, workspaces."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "gong"


def _base(cred: dict[str, Any]) -> str:
    return str(cred.get("base_url") or "https://api.gong.io").rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    key = cred.get("access_key") or cred.get("api_key")
    secret = cred.get("access_key_secret") or cred.get("api_secret")
    if not key or not secret:
        raise ValueError("Gong credential missing access_key + secret.")
    return {"Authorization": "Basic " + b64encode(f"{key}:{secret}".encode()).decode()}


async def _users(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/v2/users",
        headers=_headers(cred),
        params={"cursor": cursor} if cursor else None,
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=u["id"],
            label=f"{u.get('firstName', '')} {u.get('lastName', '')}".strip()
            or u.get("emailAddress")
            or u["id"],
            sublabel=u.get("emailAddress"),
        )
        for u in payload.get("users", [])
    ]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    next_cursor = (payload.get("records") or {}).get("cursor")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _workspaces(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/v2/workspaces", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=w["id"], label=w.get("name") or w["id"])
        for w in r.json().get("workspaces", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"users": _users, "workspaces": _workspaces}
