"""DocuSign remote-picker handlers — templates."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "docusign"


def _base(cred: dict[str, Any]) -> str:
    base = cred.get("base_url") or cred.get("account_base_url")
    if not base:
        raise ValueError("DocuSign credential missing base_url.")
    return str(base).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("DocuSign credential missing access_token.")
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


async def _templates(client, cred, params, cursor, q):  # noqa: ANN001
    account = (params.get("account_id") or cred.get("account_id") or "").strip()
    if not account:
        return LookupResponse(items=[])
    start = int(cursor) if cursor and cursor.isdigit() else 0
    r = await client.get(
        f"{_base(cred)}/v2.1/accounts/{account}/templates",
        headers=_headers(cred),
        params={"count": 100, "start_position": start, **({"search_text": q} if q else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=t["templateId"],
            label=t.get("name") or t["templateId"],
            sublabel=t.get("description"),
        )
        for t in payload.get("envelopeTemplates", [])
    ]
    total = int(payload.get("totalSetSize") or 0)
    next_cursor = str(start + 100) if start + 100 < total else None
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"templates": _templates}
