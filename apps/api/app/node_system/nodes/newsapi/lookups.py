"""NewsAPI remote-picker handlers — sources (static list from API)."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "newsapi"

_API = "https://newsapi.org/v2"


def _params_auth(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("api_key")
    if not token:
        raise ValueError("NewsAPI credential missing api_key.")
    return {"apiKey": token}


async def _sources(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/top-headlines/sources", params=_params_auth(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=s["id"], label=s.get("name") or s["id"], sublabel=s.get("category"))
        for s in r.json().get("sources", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"sources": _sources}
