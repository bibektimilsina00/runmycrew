"""Notion remote-picker handlers — databases + pages.

Notion's search endpoint returns both databases and pages in one shot,
we filter server-side with `filter.value=database/page`.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "notion"

_API = "https://api.notion.com/v1"
_PAGE_SIZE = 100


def _auth_headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Notion credential is missing an access token.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _title_of(obj: dict[str, Any]) -> str:
    """Notion titles are rich-text arrays. Concatenate `plain_text` if
    the field is populated; fall back to the object id when empty
    (untitled pages)."""
    if obj.get("object") == "database":
        title = obj.get("title") or []
    else:
        # Pages carry the title inside `properties.<title_prop>.title`
        # — Notion doesn't guarantee the property name, so find it.
        title = []
        for prop in (obj.get("properties") or {}).values():
            if prop.get("type") == "title":
                title = prop.get("title") or []
                break
    text = "".join(t.get("plain_text") or "" for t in title).strip()
    return text or "(untitled)"


async def _search(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    filter_value: str,
    cursor: str | None,
    q: str | None,
) -> LookupResponse:
    body: dict[str, Any] = {
        "filter": {"property": "object", "value": filter_value},
        "page_size": _PAGE_SIZE,
    }
    if q:
        body["query"] = q
    if cursor:
        body["start_cursor"] = cursor

    r = await client.post(f"{_API}/search", headers=_auth_headers(cred), json=body)
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=obj["id"],
            label=_title_of(obj),
            sublabel=obj.get("parent", {}).get("type", "").replace("_", " ").capitalize() or None,
        )
        for obj in payload.get("results", [])
    ]
    return LookupResponse(
        items=items,
        cursor=payload.get("next_cursor"),
        has_more=bool(payload.get("has_more")),
    )


async def _databases(client, cred, _params, cursor, q):  # noqa: ANN001
    return await _search(client, cred, "database", cursor, q)


async def _pages(client, cred, _params, cursor, q):  # noqa: ANN001
    return await _search(client, cred, "page", cursor, q)


LOOKUPS = {
    "databases": _databases,
    "pages": _pages,
}
