"""Zendesk remote-picker handlers — groups, brands, users, organizations."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "zendesk"


def _base(cred: dict[str, Any]) -> str:
    sub = cred.get("subdomain") or cred.get("base_url")
    if not sub:
        raise ValueError("Zendesk credential missing subdomain.")
    if not str(sub).startswith("http"):
        sub = f"https://{sub}.zendesk.com"
    return str(sub).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    if token := cred.get("access_token"):
        return {"Authorization": f"Bearer {token}"}
    email = cred.get("email")
    api = cred.get("api_key") or cred.get("api_token")
    if email and api:
        creds = b64encode(f"{email}/token:{api}".encode()).decode()
        return {"Authorization": f"Basic {creds}"}
    raise ValueError("Zendesk credential missing access_token or (email, api_key).")


async def _groups(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/api/v2/groups", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=str(g["id"]), label=g.get("name") or str(g["id"]))
        for g in r.json().get("groups", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _brands(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/api/v2/brands", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(
            id=str(b["id"]), label=b.get("name") or str(b["id"]), sublabel=b.get("subdomain")
        )
        for b in r.json().get("brands", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _users(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/api/v2/users",
        headers=_headers(cred),
        params={"per_page": 100, **({"page[after]": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=str(u["id"]), label=u.get("name") or str(u["id"]), sublabel=u.get("email"))
        for u in payload.get("users", [])
    ]
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    next_cursor = (payload.get("meta") or {}).get("after_cursor")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"groups": _groups, "brands": _brands, "users": _users}
