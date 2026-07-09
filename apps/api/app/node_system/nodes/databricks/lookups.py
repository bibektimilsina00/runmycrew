"""Databricks remote-picker handlers — catalogs, schemas, tables, warehouses."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "databricks"


def _base(cred: dict[str, Any]) -> str:
    host = cred.get("workspace_url") or cred.get("host") or cred.get("base_url")
    if not host:
        raise ValueError("Databricks credential missing workspace_url.")
    return str(host).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key") or cred.get("token")
    if not token:
        raise ValueError("Databricks credential missing token.")
    return {"Authorization": f"Bearer {token}"}


async def _catalogs(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/api/2.1/unity-catalog/catalogs", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=c["name"], label=c["name"], sublabel=c.get("comment"))
        for c in r.json().get("catalogs", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _schemas(client, cred, params, _cursor, q):  # noqa: ANN001
    catalog = (params.get("catalog") or params.get("catalog_name") or "").strip()
    if not catalog:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_base(cred)}/api/2.1/unity-catalog/schemas",
        headers=_headers(cred),
        params={"catalog_name": catalog},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=s["name"], label=s["name"], sublabel=s.get("comment"))
        for s in r.json().get("schemas", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _tables(client, cred, params, _cursor, q):  # noqa: ANN001
    catalog = (params.get("catalog") or "").strip()
    schema = (params.get("schema") or "").strip()
    if not catalog or not schema:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_base(cred)}/api/2.1/unity-catalog/tables",
        headers=_headers(cred),
        params={"catalog_name": catalog, "schema_name": schema},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=t["name"], label=t["name"], sublabel=t.get("table_type"))
        for t in r.json().get("tables", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _warehouses(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/api/2.0/sql/warehouses", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=w["id"], label=w.get("name") or w["id"], sublabel=w.get("state"))
        for w in r.json().get("warehouses", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"catalogs": _catalogs, "schemas": _schemas, "tables": _tables, "warehouses": _warehouses}
