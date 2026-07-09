"""Stripe remote-picker handlers — customers, products, prices."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "stripe"

_API = "https://api.stripe.com/v1"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Stripe credential missing api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _customers(client, cred, _params, cursor, q):  # noqa: ANN001
    params: dict[str, Any] = {"limit": 100}
    if cursor:
        params["starting_after"] = cursor
    if q:
        # Stripe supports search on `email:x` style
        r = await client.get(
            f"{_API}/customers/search",
            headers=_headers(cred),
            params={"query": f'email:"{q}"', "limit": 100},
        )
    else:
        r = await client.get(f"{_API}/customers", headers=_headers(cred), params=params)
    r.raise_for_status()
    payload = r.json()
    data = payload.get("data", [])
    items = [
        LookupItem(id=c["id"], label=c.get("email") or c["id"], sublabel=c.get("name"))
        for c in data
    ]
    next_cursor = data[-1]["id"] if payload.get("has_more") and data else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _products(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/products",
        headers=_headers(cred),
        params={"limit": 100, "active": "true", **({"starting_after": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    data = payload.get("data", [])
    items = [
        LookupItem(id=p["id"], label=p.get("name") or p["id"], sublabel=p.get("description"))
        for p in data
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = data[-1]["id"] if payload.get("has_more") and data else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _prices(client, cred, params, cursor, q):  # noqa: ANN001
    product = (params.get("product_id") or params.get("product") or "").strip()
    r = await client.get(
        f"{_API}/prices",
        headers=_headers(cred),
        params={
            "limit": 100,
            **({"product": product} if product else {}),
            **({"starting_after": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    data = payload.get("data", [])
    items = [
        LookupItem(
            id=p["id"],
            label=p.get("nickname") or p["id"],
            sublabel=f"{p.get('unit_amount', 0) / 100} {p.get('currency', '').upper()}",
        )
        for p in data
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = data[-1]["id"] if payload.get("has_more") and data else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"customers": _customers, "products": _products, "prices": _prices}
