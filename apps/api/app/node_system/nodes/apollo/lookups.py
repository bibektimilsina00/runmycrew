"""Apollo.io remote-picker handlers — email accounts, sequences."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "apollo"

_API = "https://api.apollo.io/v1"


def _params_auth(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key")
    if not token:
        raise ValueError("Apollo credential missing api_key.")
    return {"api_key": token}


async def _sequences(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/emailer_campaigns", params=_params_auth(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=c["id"], label=c.get("name") or c["id"], sublabel=c.get("active_state"))
        for c in r.json().get("emailer_campaigns", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _email_accounts(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/email_accounts", params=_params_auth(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=e["id"], label=e.get("email") or e["id"], sublabel=e.get("provider"))
        for e in r.json().get("email_accounts", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"sequences": _sequences, "email_accounts": _email_accounts}
