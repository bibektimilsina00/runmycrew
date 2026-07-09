"""Mailgun remote-picker handlers — domains, mailing lists."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "mailgun"


def _base(cred: dict[str, Any]) -> str:
    region = (cred.get("region") or "us").lower()
    return "https://api.eu.mailgun.net/v3" if region == "eu" else "https://api.mailgun.net/v3"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    api = cred.get("api_key") or cred.get("access_token")
    if not api:
        raise ValueError("Mailgun credential missing api_key.")
    return {"Authorization": "Basic " + b64encode(f"api:{api}".encode()).decode()}


async def _domains(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/domains", headers=_headers(cred), params={"limit": 100})
    r.raise_for_status()
    items = [
        LookupItem(id=d["name"], label=d["name"], sublabel=d.get("state"))
        for d in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _mailing_lists(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/lists/pages", headers=_headers(cred), params={"limit": 100}
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=lst["address"], label=lst.get("name") or lst["address"], sublabel=lst["address"]
        )
        for lst in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"domains": _domains, "mailing_lists": _mailing_lists}
