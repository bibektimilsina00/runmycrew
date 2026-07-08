"""Ashby remote-picker handlers — jobs, users, offices, departments."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "ashby"

_API = "https://api.ashbyhq.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    key = cred.get("api_key")
    if not key:
        raise ValueError("Ashby credential missing api_key.")
    return {
        "Authorization": "Basic " + b64encode(f"{key}:".encode()).decode(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


async def _list(client, cred, path, extract_key, q):
    r = await client.post(f"{_API}{path}", headers=_headers(cred), json={"limit": 100})
    r.raise_for_status()
    data = r.json().get("results", [])
    items = [
        LookupItem(
            id=x["id"],
            label=x.get("name") or x.get("title") or x["id"],
            sublabel=x.get("status") or x.get("stage"),
        )
        for x in (data if isinstance(data, list) else [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _jobs(client, cred, _params, _cursor, q):  # noqa: ANN001
    return await _list(client, cred, "/job.list", "id", q)


async def _users(client, cred, _params, _cursor, q):  # noqa: ANN001
    return await _list(client, cred, "/user.list", "id", q)


async def _departments(client, cred, _params, _cursor, q):  # noqa: ANN001
    return await _list(client, cred, "/department.list", "id", q)


LOOKUPS = {"jobs": _jobs, "users": _users, "departments": _departments}
