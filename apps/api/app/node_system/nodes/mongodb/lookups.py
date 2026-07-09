"""MongoDB Atlas remote-picker handlers — clusters, databases, collections.

Uses Atlas Admin API for cluster/database discovery. Actual query
execution is handled by the mongodb node itself.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "mongodb"

_ADMIN = "https://cloud.mongodb.com/api/atlas/v2"


def _digest_auth(cred: dict[str, Any]) -> tuple[str, str] | None:
    pub = cred.get("public_key")
    priv = cred.get("private_key")
    if pub and priv:
        return (pub, priv)
    return None


async def _projects(client, cred, _params, _cursor, q):  # noqa: ANN001
    auth = _digest_auth(cred)
    if not auth:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_ADMIN}/groups",
        auth=auth,
        headers={"Accept": "application/vnd.atlas.2024-08-05+json"},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=g["id"], label=g.get("name") or g["id"]) for g in r.json().get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _clusters(client, cred, params, _cursor, q):  # noqa: ANN001
    project = (params.get("project_id") or params.get("group_id") or "").strip()
    auth = _digest_auth(cred)
    if not project or not auth:
        return LookupResponse(items=[])
    r = await client.get(
        f"{_ADMIN}/groups/{project}/clusters",
        auth=auth,
        headers={"Accept": "application/vnd.atlas.2024-08-05+json"},
    )
    r.raise_for_status()
    items = [
        LookupItem(id=c["name"], label=c.get("name") or c["id"], sublabel=c.get("stateName"))
        for c in r.json().get("results", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"projects": _projects, "clusters": _clusters}
