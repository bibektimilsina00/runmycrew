"""Mailchimp remote-picker handlers — audiences (lists)."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "mailchimp"


def _base(cred: dict[str, Any]) -> str:
    dc = cred.get("data_center") or cred.get("dc")
    if not dc:
        # Extract from api_key suffix (`xxxxxxxx-us12`).
        key = cred.get("api_key") or ""
        if "-" in key:
            dc = key.rsplit("-", 1)[-1]
    if not dc:
        raise ValueError("Mailchimp credential missing data_center (or `-us12` suffix on api_key).")
    return f"https://{dc}.api.mailchimp.com/3.0"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("Mailchimp credential missing api_key / access_token.")
    scheme = "Bearer" if cred.get("access_token") else "apikey"
    if scheme == "apikey":
        # Mailchimp basic-auth alt: anystring:apikey
        from base64 import b64encode

        return {"Authorization": "Basic " + b64encode(f"anystring:{token}".encode()).decode()}
    return {"Authorization": f"Bearer {token}"}


async def _audiences(client, cred, _params, cursor, q):  # noqa: ANN001
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_base(cred)}/lists",
        headers=_headers(cred),
        params={"count": 50, "offset": offset, "fields": "lists.id,lists.name,total_items"},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=lst["id"], label=lst.get("name") or lst["id"])
        for lst in payload.get("lists", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    total = payload.get("total_items", 0)
    next_cursor = str(offset + 50) if offset + 50 < total else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"audiences": _audiences, "lists": _audiences}
