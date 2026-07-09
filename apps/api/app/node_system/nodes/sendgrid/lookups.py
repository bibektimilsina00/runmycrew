"""SendGrid remote-picker handlers — lists, templates."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "sendgrid"

_API = "https://api.sendgrid.com/v3"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("SendGrid credential missing api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _lists(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/marketing/lists",
        headers=_headers(cred),
        params={"page_size": 100, **({"page_token": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=lst["id"], label=lst.get("name") or lst["id"], sublabel=str(lst.get("contact_count"))
        )
        for lst in payload.get("result", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _templates(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_API}/templates", headers=_headers(cred), params={"generations": "dynamic"}
    )
    r.raise_for_status()
    items = [
        LookupItem(id=t["id"], label=t.get("name") or t["id"]) for t in r.json().get("result", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"lists": _lists, "templates": _templates}
