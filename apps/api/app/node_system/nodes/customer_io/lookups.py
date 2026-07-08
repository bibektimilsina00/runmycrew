"""Customer.io remote-picker handlers — segments, campaigns."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "customer_io"


def _base(cred: dict[str, Any]) -> str:
    region = (cred.get("region") or "us").lower()
    return (
        "https://beta-api.customer.io/v1"
        if region == "us"
        else "https://beta-api-eu.customer.io/v1"
    )


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("app_api_key") or cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Customer.io credential missing app_api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _segments(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/segments", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(s["id"]), label=s.get("name") or str(s["id"]), sublabel=s.get("type"))
        for s in r.json().get("segments", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _campaigns(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/campaigns", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(c["id"]), label=c.get("name") or str(c["id"]), sublabel=c.get("state"))
        for c in r.json().get("campaigns", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"segments": _segments, "campaigns": _campaigns}
