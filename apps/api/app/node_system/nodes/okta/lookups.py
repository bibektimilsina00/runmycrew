"""Okta remote-picker handlers — users, groups, apps."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "okta"


def _base(cred: dict[str, Any]) -> str:
    dom = cred.get("okta_domain") or cred.get("base_url") or cred.get("host")
    if not dom:
        raise ValueError("Okta credential missing okta_domain.")
    dom = str(dom).rstrip("/")
    if not dom.startswith("http"):
        dom = f"https://{dom}"
    return dom


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Okta credential missing api_key.")
    scheme = "SSWS" if cred.get("api_key") else "Bearer"
    return {"Authorization": f"{scheme} {token}", "Accept": "application/json"}


async def _users(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/api/v1/users",
        headers=_headers(cred),
        params={"limit": 200, **({"after": cursor} if cursor else {}), **({"q": q} if q else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=u["id"],
            label=(u.get("profile") or {}).get("login") or u["id"],
            sublabel=(u.get("profile") or {}).get("email"),
        )
        for u in r.json()
    ]
    # Okta returns Link headers; parse next cursor from `rel="next"`
    link = r.headers.get("link", "")
    next_cursor = None
    for part in link.split(","):
        if 'rel="next"' in part and "after=" in part:
            next_cursor = part.split("after=")[1].split(">")[0].split("&")[0]
            break
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _groups(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/api/v1/groups",
        headers=_headers(cred),
        params={"limit": 200, **({"q": q} if q else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=g["id"],
            label=(g.get("profile") or {}).get("name") or g["id"],
            sublabel=(g.get("profile") or {}).get("description"),
        )
        for g in r.json()
    ]
    return LookupResponse(items=items)


async def _apps(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/api/v1/apps",
        headers=_headers(cred),
        params={"limit": 200, **({"q": q} if q else {})},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=a["id"], label=a.get("label") or a["id"], sublabel=a.get("name"))
        for a in r.json()
    ]
    return LookupResponse(items=items)


LOOKUPS = {"users": _users, "groups": _groups, "apps": _apps}
