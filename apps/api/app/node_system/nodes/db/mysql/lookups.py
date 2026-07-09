"""MySQL remote-picker handlers — schemas, tables, columns.

Uses `aiomysql` — installed as a workspace dep. Same shape as the
postgres handler: short-lived connection per lookup, introspect via
`information_schema`.
"""

from __future__ import annotations

from typing import Any

import aiomysql

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "mysql"


def _connect_kwargs(cred: dict[str, Any]) -> dict[str, Any]:
    if dsn := cred.get("connectionString") or cred.get("connection_string") or cred.get("dsn"):
        # Parse mysql://user:pass@host:port/db
        from urllib.parse import urlparse

        u = urlparse(dsn)
        return {
            "host": u.hostname,
            "port": u.port or 3306,
            "user": u.username,
            "password": u.password,
            "db": (u.path or "/").lstrip("/") or None,
        }
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
        kwargs["db"] = db
    if not kwargs.get("host"):
        raise ValueError("MySQL credential missing connectionString or host.")
    return kwargs


async def _fetch(cred, sql, *args):
    conn = await aiomysql.connect(**_connect_kwargs(cred), connect_timeout=10)
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchall()
    finally:
        conn.close()


async def _schemas(_client, cred, _params, _cursor, q):  # noqa: ANN001
    rows = await _fetch(
        cred,
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name NOT IN ('mysql','performance_schema','information_schema','sys') "
        "ORDER BY schema_name",
    )
    items = [LookupItem(id=r["schema_name"], label=r["schema_name"]) for r in rows]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _tables(_client, cred, params, _cursor, q):  # noqa: ANN001
    schema = (params.get("schema") or params.get("database") or "").strip()
    if not schema:
        return LookupResponse(items=[])
    rows = await _fetch(
        cred,
        "SELECT table_name, table_type FROM information_schema.tables "
        "WHERE table_schema = %s ORDER BY table_name",
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
    schema = (params.get("schema") or "").strip()
    table = (params.get("table") or "").strip()
    if not schema or not table:
        return LookupResponse(items=[])
    rows = await _fetch(
        cred,
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
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
