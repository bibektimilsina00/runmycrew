"""MessageBird / Bird remote-picker handlers — channels, contacts lists."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "messagebird"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("api_key")
    if not token:
        raise ValueError("MessageBird credential missing api_key.")
    return {"Authorization": f"AccessKey {token}"}


async def _channels(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://conversations.messagebird.com/v1/channels", headers=_headers(cred)
    )
    r.raise_for_status()
    items = [
        LookupItem(id=c["id"], label=c.get("name") or c["id"], sublabel=c.get("platformId"))
        for c in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"channels": _channels}
