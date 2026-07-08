"""Amplitude remote-picker handlers — cohorts."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "amplitude"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    api = cred.get("api_key")
    secret = cred.get("secret_key") or cred.get("secret") or cred.get("api_secret")
    if not api or not secret:
        raise ValueError("Amplitude credential missing api_key + secret_key.")
    return {"Authorization": "Basic " + b64encode(f"{api}:{secret}".encode()).decode()}


async def _cohorts(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get("https://amplitude.com/api/3/cohorts", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(
            id=c["id"],
            label=c.get("name") or c["id"],
            sublabel=c.get("description"),
        )
        for c in r.json().get("cohorts", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"cohorts": _cohorts}
