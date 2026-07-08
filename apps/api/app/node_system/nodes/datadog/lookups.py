"""Datadog remote-picker handlers — dashboards, monitors, metrics."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "datadog"


def _base(cred: dict[str, Any]) -> str:
    site = cred.get("site") or "datadoghq.com"
    return f"https://api.{site}"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    api_key = cred.get("api_key") or cred.get("access_token")
    app_key = cred.get("application_key") or cred.get("app_key")
    if not api_key or not app_key:
        raise ValueError("Datadog credential missing api_key + application_key.")
    return {
        "DD-API-KEY": api_key,
        "DD-APPLICATION-KEY": app_key,
        "Accept": "application/json",
    }


async def _dashboards(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/api/v1/dashboard", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=d["id"], label=d.get("title") or d["id"], sublabel=d.get("description"))
        for d in r.json().get("dashboards", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _monitors(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/api/v1/monitor", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(m["id"]), label=m.get("name") or str(m["id"]), sublabel=m.get("type"))
        for m in r.json()
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"dashboards": _dashboards, "monitors": _monitors}
