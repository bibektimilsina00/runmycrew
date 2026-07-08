"""Loops.so remote-picker handlers — mailing lists."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "loops"

_API = "https://app.loops.so/api/v1"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Loops credential missing api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _mailing_lists(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/lists", headers=_headers(cred))
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        data = data.get("data", []) or data.get("lists", [])
    items = [LookupItem(id=str(m["id"]), label=m.get("name") or str(m["id"])) for m in data]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"mailing_lists": _mailing_lists}
