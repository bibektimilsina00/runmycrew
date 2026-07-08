"""ClickHouse Cloud remote-picker handlers — databases + tables.

Uses ClickHouse's HTTP interface (`?query=SHOW ...&default_format=JSON`).
"""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "clickhouse"


def _base(cred: dict[str, Any]) -> str:
    host = cred.get("host") or cred.get("base_url")
    if not host:
        raise ValueError("ClickHouse credential missing host.")
    host = str(host).rstrip("/")
    if not host.startswith("http"):
        host = f"https://{host}"
    return host


def _auth(cred: dict[str, Any]) -> tuple[str, str] | None:
    user = cred.get("username") or cred.get("user")
    pw = cred.get("password") or cred.get("api_key")
    if user is not None and pw is not None:
        return (user, pw)
    return None


async def _run(client, cred, sql):
    auth = _auth(cred)
    r = await client.get(
        _base(cred),
        params={"query": sql, "default_format": "JSON"},
        **({"auth": auth} if auth else {}),
    )
    r.raise_for_status()
    return r.json()


async def _databases(client, cred, _params, _cursor, q):  # noqa: ANN001
    data = await _run(client, cred, "SHOW DATABASES")
    items = [LookupItem(id=row["name"], label=row["name"]) for row in data.get("data", [])]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _tables(client, cred, params, _cursor, q):  # noqa: ANN001
    db = (params.get("database") or "").strip()
    if not db:
        return LookupResponse(items=[])
    # Backticks + sanitize db name (letters/digits/underscore only).
    if not db.replace("_", "").isalnum():
        return LookupResponse(items=[])
    data = await _run(client, cred, f"SHOW TABLES FROM `{db}`")
    items = [LookupItem(id=row["name"], label=row["name"]) for row in data.get("data", [])]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"databases": _databases, "tables": _tables}
