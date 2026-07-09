"""Supabase remote-picker handlers — projects, storage buckets."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "supabase"


def _base(cred: dict[str, Any]) -> str:
    url = cred.get("project_url") or cred.get("base_url")
    if not url:
        raise ValueError("Supabase credential missing project_url.")
    return str(url).rstrip("/")


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("service_role_key") or cred.get("api_key") or cred.get("anon_key")
    if not token:
        raise ValueError("Supabase credential missing service_role_key / api_key.")
    return {"Authorization": f"Bearer {token}", "apikey": token}


async def _buckets(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_base(cred)}/storage/v1/bucket", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(
            id=b["name"],
            label=b["name"],
            sublabel="public" if b.get("public") else "private",
        )
        for b in r.json()
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


# Supabase's Postgres schema listing needs the pgREST endpoint, which
# doesn't expose an introspection endpoint by default — surface a
# useful subset via the Management API when a personal access token
# is on the credential.
async def _projects(client, cred, _params, _cursor, q):  # noqa: ANN001
    token = cred.get("management_api_key")
    if not token:
        return LookupResponse(items=[])
    r = await client.get(
        "https://api.supabase.com/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=p["id"], label=p.get("name") or p["id"], sublabel=p.get("region"))
        for p in r.json()
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"buckets": _buckets, "projects": _projects}
