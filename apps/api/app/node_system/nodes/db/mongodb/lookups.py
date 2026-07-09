"""MongoDB remote-picker handlers — databases + collections.

Uses `motor` (async pymongo). Handlers open a short-lived client per
lookup — no pool, no cache. Assumes the credential has either
`connectionString` (full URI) or host/port/user/password fields.
"""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "mongodb"


def _uri(cred: dict[str, Any]) -> str:
    if dsn := cred.get("connectionString") or cred.get("connection_string") or cred.get("uri"):
        return str(dsn)
    host = cred.get("host") or "localhost"
    port = cred.get("port") or 27017
    user = cred.get("user") or cred.get("username") or ""
    pw = cred.get("password") or ""
    auth = f"{user}:{pw}@" if user else ""
    return f"mongodb://{auth}{host}:{port}"


async def _databases(_client, cred, _params, _cursor, q):  # noqa: ANN001
    client = AsyncIOMotorClient(_uri(cred), serverSelectionTimeoutMS=10_000)
    try:
        names = await client.list_database_names()
    finally:
        client.close()
    items = [LookupItem(id=n, label=n) for n in names if n not in ("admin", "local", "config")]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _collections(_client, cred, params, _cursor, q):  # noqa: ANN001
    db_name = (params.get("database") or params.get("db") or "").strip()
    if not db_name:
        return LookupResponse(items=[])
    client = AsyncIOMotorClient(_uri(cred), serverSelectionTimeoutMS=10_000)
    try:
        names = await client[db_name].list_collection_names()
    finally:
        client.close()
    items = [LookupItem(id=n, label=n) for n in sorted(names)]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"databases": _databases, "collections": _collections}
