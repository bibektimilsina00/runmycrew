"""PagerDuty remote-picker handlers — services, escalation policies, users."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "pagerduty"

_API = "https://api.pagerduty.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("PagerDuty credential missing api_key.")
    return {
        "Authorization": f"Token token={token}",
        "Accept": "application/vnd.pagerduty+json;version=2",
    }


async def _paged(client, cred, path):
    r = await client.get(f"{_API}{path}", headers=_headers(cred), params={"limit": 100})
    r.raise_for_status()
    return r.json()


async def _services(client, cred, _params, _cursor, q):  # noqa: ANN001
    data = await _paged(client, cred, "/services")
    items = [
        LookupItem(id=s["id"], label=s.get("name") or s["id"], sublabel=s.get("status"))
        for s in data.get("services", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _escalation_policies(client, cred, _params, _cursor, q):  # noqa: ANN001
    data = await _paged(client, cred, "/escalation_policies")
    items = [
        LookupItem(id=p["id"], label=p.get("name") or p["id"])
        for p in data.get("escalation_policies", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _users(client, cred, _params, _cursor, q):  # noqa: ANN001
    data = await _paged(client, cred, "/users")
    items = [
        LookupItem(id=u["id"], label=u.get("name") or u["id"], sublabel=u.get("email"))
        for u in data.get("users", [])
    ]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    return LookupResponse(items=items)


LOOKUPS = {"services": _services, "escalation_policies": _escalation_policies, "users": _users}
