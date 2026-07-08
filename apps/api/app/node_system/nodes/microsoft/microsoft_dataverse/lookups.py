"""Microsoft Dataverse remote-picker handlers — entities/tables."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "dataverse"


def _base(cred: dict[str, Any]) -> str:
    org = cred.get("organization_url") or cred.get("base_url")
    if not org:
        raise ValueError("Dataverse credential missing organization_url.")
    return str(org).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Dataverse credential missing access_token.")
    return {
        "Authorization": f"Bearer {token}",
        "OData-Version": "4.0",
        "Accept": "application/json",
    }


async def _entities(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        f"{_base(cred)}/api/data/v9.2/EntityDefinitions",
        headers=_headers(cred),
        params={
            "$select": "LogicalName,DisplayName,EntitySetName",
            "$filter": "IsCustomizable/Value eq true",
        },
    )
    r.raise_for_status()
    items = []
    for e in r.json().get("value", []):
        display = ((e.get("DisplayName") or {}).get("UserLocalizedLabel") or {}).get("Label") or e[
            "LogicalName"
        ]
        items.append(
            LookupItem(id=e["LogicalName"], label=display, sublabel=e.get("EntitySetName"))
        )
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"entities": _entities}
