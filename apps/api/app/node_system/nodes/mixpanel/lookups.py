"""Mixpanel remote-picker handlers — projects (limited by API)."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "mixpanel"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    sa = cred.get("service_account_username")
    sp = cred.get("service_account_secret") or cred.get("api_secret")
    if sa and sp:
        return {"Authorization": "Basic " + b64encode(f"{sa}:{sp}".encode()).decode()}
    token = cred.get("api_key") or cred.get("access_token")
    if not token:
        raise ValueError("Mixpanel credential missing service-account or api_key.")
    return {"Authorization": f"Bearer {token}"}


async def _saved_reports(client, cred, params, _cursor, q):  # noqa: ANN001
    project_id = (params.get("project_id") or "").strip()
    if not project_id:
        return LookupResponse(items=[])
    r = await client.get(
        "https://mixpanel.com/api/2.0/bookmarks/list",
        headers=_headers(cred),
        params={"project_id": project_id},
    )
    r.raise_for_status()
    items = [LookupItem(id=str(b["id"]), label=b.get("name") or str(b["id"])) for b in r.json()]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"saved_reports": _saved_reports}
