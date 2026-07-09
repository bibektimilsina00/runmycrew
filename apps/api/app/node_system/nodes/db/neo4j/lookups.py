"""Neo4j remote-picker handlers — databases, node labels, relationship types."""

from __future__ import annotations

from typing import Any

from neo4j import AsyncGraphDatabase

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "neo4j"


def _uri_auth(cred: dict[str, Any]) -> tuple[str, tuple[str, str] | None]:
    uri = cred.get("uri") or cred.get("connectionString") or cred.get("host")
    if not uri:
        raise ValueError("Neo4j credential missing uri.")
    if not str(uri).startswith(("bolt", "neo4j")):
        uri = f"bolt://{uri}"
    user = cred.get("user") or cred.get("username")
    pw = cred.get("password")
    auth = (user, pw) if user and pw else None
    return str(uri), auth


async def _run(cred, cypher):
    uri, auth = _uri_auth(cred)
    driver = AsyncGraphDatabase.driver(uri, auth=auth)
    try:
        async with driver.session() as session:
            result = await session.run(cypher)
            return [dict(r) async for r in result]
    finally:
        await driver.close()


async def _databases(_client, cred, _params, _cursor, q):  # noqa: ANN001
    rows = await _run(cred, "SHOW DATABASES")
    items = [
        LookupItem(
            id=r.get("name", ""),
            label=r.get("name", ""),
            sublabel=r.get("currentStatus") or r.get("role"),
        )
        for r in rows
        if r.get("name") not in ("system",)
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _labels(_client, cred, _params, _cursor, q):  # noqa: ANN001
    rows = await _run(cred, "CALL db.labels() YIELD label RETURN label ORDER BY label")
    items = [LookupItem(id=r["label"], label=r["label"]) for r in rows]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _relationship_types(_client, cred, _params, _cursor, q):  # noqa: ANN001
    rows = await _run(
        cred,
        "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType",
    )
    items = [LookupItem(id=r["relationshipType"], label=r["relationshipType"]) for r in rows]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {
    "databases": _databases,
    "labels": _labels,
    "relationship_types": _relationship_types,
}
