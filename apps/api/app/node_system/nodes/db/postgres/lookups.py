"""Postgres remote-picker handlers — schemas, tables.

Uses `asyncpg` (already a workspace dep) to connect via the credential
dict's `connectionString` / `host`+`port`+`user`+`password`+`database`.
Handlers open a short-lived connection per lookup — no pool, no cache.
Introspects via `information_schema`.
"""

from __future__ import annotations

from typing import Any

import asyncpg

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "postgres"


def _connect_kwargs(cred: dict[str, Any]) -> dict[str, Any]:
    """Extract asyncpg-compatible kwargs from a credential dict.
    Prefers a full `connectionString`; otherwise builds from parts."""
    if dsn := cred.get("connectionString") or cred.get("connection_string") or cred.get("dsn"):
        return {"dsn": dsn}
    kwargs: dict[str, Any] = {}
    if host := cred.get("host"):
        kwargs["host"] = host
    if port := cred.get("port"):
        kwargs["port"] = int(port) if isinstance(port, str) else port
    if user := cred.get("user") or cred.get("username"):
        kwargs["user"] = user
    if pw := cred.get("password"):
        kwargs["password"] = pw
    if db := cred.get("database") or cred.get("db"):
        kwargs["database"] = db
    if cred.get("ssl") is True:
        kwargs["ssl"] = "require"
    if not kwargs.get("host") and "dsn" not in kwargs:
        raise ValueError("Postgres credential missing connectionString or host.")
    return kwargs


async def _run_query(cred: dict[str, Any], sql: str, *args) -> list[dict[str, Any]]:
    kwargs = _connect_kwargs(cred)
    conn = await asyncpg.connect(**kwargs, timeout=10)
    try:
        rows = await conn.fetch(sql, *args)
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def _schemas(_client, cred, _params, _cursor, q):  # noqa: ANN001
    rows = await _run_query(
        cred,
        """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
          AND schema_name NOT LIKE 'pg_%'
        ORDER BY schema_name
        """,
    )
    items = [LookupItem(id=r["schema_name"], label=r["schema_name"]) for r in rows]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _tables(_client, cred, params, _cursor, q):  # noqa: ANN001
    schema = (params.get("schema") or params.get("schema_name") or "public").strip() or "public"
    rows = await _run_query(
        cred,
        """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = $1
        ORDER BY table_name
        """,
        schema,
    )
    items = [
        LookupItem(id=r["table_name"], label=r["table_name"], sublabel=r.get("table_type"))
        for r in rows
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _columns(_client, cred, params, _cursor, q):  # noqa: ANN001
    schema = (params.get("schema") or "public").strip() or "public"
    table = (params.get("table") or params.get("table_name") or "").strip()
    if not table:
        return LookupResponse(items=[])
    rows = await _run_query(
        cred,
        """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position
        """,
        schema,
        table,
    )
    items = [
        LookupItem(
            id=r["column_name"],
            label=r["column_name"],
            sublabel=f"{r['data_type']}{' NULL' if r['is_nullable'] == 'YES' else ''}",
        )
        for r in rows
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"schemas": _schemas, "tables": _tables, "columns": _columns}
