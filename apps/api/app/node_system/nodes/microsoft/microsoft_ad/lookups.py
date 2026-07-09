"""Microsoft AD / Entra ID remote-picker handlers — groups, users.

Same Graph endpoints as `nodes/microsoft/lookups.py` but exposed via a
separate provider key so AD-specific fields don't compete with Teams.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "microsoft_ad"

_GRAPH = "https://graph.microsoft.com/v1.0"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Microsoft AD credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _groups(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_GRAPH}/groups",
        headers=_headers(cred),
        params={"$top": 100, **({"$search": f'"displayName:{q}"'} if q else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=g["id"], label=g.get("displayName") or g["id"], sublabel=g.get("mail"))
        for g in r.json().get("value", [])
    ]
    return LookupResponse(items=items)


async def _users(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_GRAPH}/users",
        headers=_headers(cred),
        params={"$top": 100, **({"$search": f'"displayName:{q}"'} if q else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=u["id"],
            label=u.get("displayName") or u["id"],
            sublabel=u.get("userPrincipalName") or u.get("mail"),
        )
        for u in r.json().get("value", [])
    ]
    return LookupResponse(items=items)


LOOKUPS = {"groups": _groups, "users": _users}
