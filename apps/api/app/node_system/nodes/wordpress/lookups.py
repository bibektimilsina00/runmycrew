"""WordPress remote-picker handlers — categories, tags, users, pages."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "wordpress"


def _base(cred: dict[str, Any]) -> str:
    base = cred.get("base_url") or cred.get("site_url")
    if not base:
        raise ValueError("WordPress credential missing base_url / site_url.")
    return str(base).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    if token := cred.get("access_token"):
        return {"Authorization": f"Bearer {token}"}
    user = cred.get("username") or cred.get("user")
    pw = cred.get("password") or cred.get("application_password") or cred.get("api_key")
    if user and pw:
        return {"Authorization": "Basic " + b64encode(f"{user}:{pw}".encode()).decode()}
    raise ValueError("WordPress credential missing access_token or (username, password).")


async def _terms(client, cred, taxonomy, cursor, q):
    page = int(cursor) if cursor and cursor.isdigit() else 1
    r = await client.get(
        f"{_base(cred)}/wp-json/wp/v2/{taxonomy}",
        headers=_headers(cred),
        params={"per_page": 100, "page": page, **({"search": q} if q else {})},
    )
    r.raise_for_status()
    total_pages = int(r.headers.get("X-WP-TotalPages", "1"))
    items = [
        LookupItem(id=str(t["id"]), label=t.get("name") or str(t["id"]), sublabel=t.get("slug"))
        for t in r.json()
    ]
    next_cursor = str(page + 1) if page < total_pages else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _categories(client, cred, _params, cursor, q):  # noqa: ANN001
    return await _terms(client, cred, "categories", cursor, q)


async def _tags(client, cred, _params, cursor, q):  # noqa: ANN001
    return await _terms(client, cred, "tags", cursor, q)


async def _users(client, cred, _params, cursor, q):  # noqa: ANN001
    page = int(cursor) if cursor and cursor.isdigit() else 1
    r = await client.get(
        f"{_base(cred)}/wp-json/wp/v2/users",
        headers=_headers(cred),
        params={"per_page": 100, "page": page, **({"search": q} if q else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=str(u["id"]), label=u.get("name") or str(u["id"]), sublabel=u.get("slug"))
        for u in r.json()
    ]
    total_pages = int(r.headers.get("X-WP-TotalPages", "1"))
    next_cursor = str(page + 1) if page < total_pages else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"categories": _categories, "tags": _tags, "users": _users}
