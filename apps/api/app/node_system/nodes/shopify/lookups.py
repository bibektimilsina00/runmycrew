"""Shopify remote-picker handlers — locations, collections, products."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "shopify"


def _base(cred: dict[str, Any]) -> str:
    shop = cred.get("shop_domain") or cred.get("shop") or cred.get("base_url")
    if not shop:
        raise ValueError("Shopify credential missing shop_domain.")
    shop = str(shop).rstrip("/")
    if not shop.startswith("http"):
        shop = f"https://{shop}"
    return shop


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Shopify credential missing access_token.")
    return {"X-Shopify-Access-Token": token}


async def _locations(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/admin/api/2024-10/locations.json", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(
            id=str(lst["id"]), label=lst.get("name") or str(lst["id"]), sublabel=lst.get("address1")
        )
        for lst in r.json().get("locations", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _collections(client, cred, _params, cursor, q):  # noqa: ANN001
    params: dict[str, Any] = {"limit": 100}
    if cursor:
        params["page_info"] = cursor
    r = await client.get(
        f"{_base(cred)}/admin/api/2024-10/custom_collections.json",
        headers=_headers(cred),
        params=params,
    )
    r.raise_for_status()
    items = [
        LookupItem(id=str(c["id"]), label=c.get("title") or str(c["id"]))
        for c in r.json().get("custom_collections", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _products(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/admin/api/2024-10/products.json",
        headers=_headers(cred),
        params={"limit": 100, **({"page_info": cursor} if cursor else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=str(p["id"]), label=p.get("title") or str(p["id"]), sublabel=p.get("status"))
        for p in r.json().get("products", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"locations": _locations, "collections": _collections, "products": _products}
