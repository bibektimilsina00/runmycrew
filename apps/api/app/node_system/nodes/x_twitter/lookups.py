"""X / Twitter remote-picker handlers — lists, tweets."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "x_twitter"

_API = "https://api.twitter.com/2"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("bearer_token") or cred.get("api_key")
    if not token:
        raise ValueError("X credential missing access_token / bearer_token.")
    return {"Authorization": f"Bearer {token}"}


async def _lists(client, cred, _params, _cursor, q):  # noqa: ANN001
    me_r = await client.get(f"{_API}/users/me", headers=_headers(cred))
    me_r.raise_for_status()
    uid = me_r.json()["data"]["id"]
    r = await client.get(
        f"{_API}/users/{uid}/owned_lists",
        headers=_headers(cred),
        params={"max_results": 100},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=lst["id"], label=lst.get("name") or lst["id"])
        for lst in r.json().get("data", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"lists": _lists}
