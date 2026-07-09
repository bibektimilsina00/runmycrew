"""Cloudflare remote-picker handlers — accounts, zones."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "cloudflare"

_API = "https://api.cloudflare.com/client/v4"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_token") or cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Cloudflare credential missing api_token.")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def _accounts(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/accounts", headers=_headers(cred), params={"per_page": 50})
    r.raise_for_status()
    items = [
        LookupItem(id=a["id"], label=a.get("name") or a["id"], sublabel=a.get("type"))
        for a in r.json().get("result", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _zones(client, cred, params, _cursor, q):  # noqa: ANN001
    account_id = (params.get("account_id") or "").strip()
    r = await client.get(
        f"{_API}/zones",
        headers=_headers(cred),
        params={
            "per_page": 50,
            **({"account.id": account_id} if account_id else {}),
            **({"name": q} if q else {}),
        },
    )
    r.raise_for_status()
    items = [
        LookupItem(id=z["id"], label=z.get("name") or z["id"], sublabel=z.get("status"))
        for z in r.json().get("result", [])
    ]
    return LookupResponse(items=items)


LOOKUPS = {"accounts": _accounts, "zones": _zones}
