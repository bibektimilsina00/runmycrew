"""Salesforce remote-picker handlers — sObjects (types) + reports."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "salesforce"


def _base(cred: dict[str, Any]) -> str:
    inst = cred.get("instance_url") or cred.get("base_url")
    if not inst:
        raise ValueError("Salesforce credential missing instance_url.")
    return str(inst).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Salesforce credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _objects(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/services/data/v58.0/sobjects",
        headers=_headers(cred),
    )
    r.raise_for_status()
    items = [
        LookupItem(id=s["name"], label=s.get("label") or s["name"], sublabel=s["name"])
        for s in r.json().get("sobjects", [])
        if s.get("queryable")
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _reports(client, cred, _params, _cursor, q):  # noqa: ANN001
    # Query Report SObject records via SOQL.
    soql = "SELECT Id, Name, DeveloperName FROM Report ORDER BY LastModifiedDate DESC LIMIT 200"
    r = await client.get(
        f"{_base(cred)}/services/data/v58.0/query",
        headers=_headers(cred),
        params={"q": soql},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=rec["Id"], label=rec.get("Name") or rec["Id"], sublabel=rec.get("DeveloperName")
        )
        for rec in r.json().get("records", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"objects": _objects, "reports": _reports}
