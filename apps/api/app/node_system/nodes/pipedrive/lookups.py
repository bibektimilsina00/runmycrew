"""Pipedrive remote-picker handlers — pipelines, stages, users."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "pipedrive"


def _base(cred: dict[str, Any]) -> str:
    return str(
        cred.get("base_url") or cred.get("company_domain") or "https://api.pipedrive.com"
    ).rstrip("/")


def _params_auth(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Pipedrive credential missing api_key.")
    return {"api_token": token}


async def _pipelines(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/v1/pipelines", params=_params_auth(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(p["id"]), label=p.get("name") or str(p["id"]))
        for p in r.json().get("data", []) or []
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _stages(client, cred, params, _cursor, q):  # noqa: ANN001
    pipeline = (params.get("pipeline_id") or "").strip()
    query = {**_params_auth(cred)}
    if pipeline:
        query["pipeline_id"] = pipeline
    r = await client.get(f"{_base(cred)}/v1/stages", params=query)
    r.raise_for_status()
    items = [
        LookupItem(
            id=str(s["id"]), label=s.get("name") or str(s["id"]), sublabel=str(s.get("order_nr"))
        )
        for s in r.json().get("data", []) or []
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _users(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/v1/users", params=_params_auth(cred))
    r.raise_for_status()
    items = [
        LookupItem(
            id=str(u["id"]),
            label=u.get("name") or str(u["id"]),
            sublabel=u.get("email"),
        )
        for u in r.json().get("data", []) or []
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"pipelines": _pipelines, "stages": _stages, "users": _users}
