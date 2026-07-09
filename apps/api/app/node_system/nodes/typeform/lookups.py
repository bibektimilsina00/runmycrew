"""Typeform remote-picker handlers — forms."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "typeform"

_API = "https://api.typeform.com"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Typeform credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _forms(client, cred, _params, cursor, q):  # noqa: ANN001
    page = int(cursor) if cursor and cursor.isdigit() else 1
    r = await client.get(
        f"{_API}/forms",
        headers=_headers(cred),
        params={
            "page_size": 100,
            "page": page,
            **({"search": q} if q else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=f["id"], label=f.get("title") or f["id"], sublabel=f.get("last_updated_at"))
        for f in payload.get("items", [])
    ]
    page_count = payload.get("page_count", 1)
    next_cursor = str(page + 1) if page < page_count else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"forms": _forms}
