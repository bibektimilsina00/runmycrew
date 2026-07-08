"""EmailBison remote-picker handlers — campaigns."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "emailbison"

_API = "https://app.emailbison.com/api"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("EmailBison credential missing api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _campaigns(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/v1/campaigns", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(c["id"]), label=c.get("name") or str(c["id"]))
        for c in r.json().get("data", []) or []
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"campaigns": _campaigns}
