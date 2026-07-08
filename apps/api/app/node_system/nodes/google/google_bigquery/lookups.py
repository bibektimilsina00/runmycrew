"""BigQuery remote-picker handlers — datasets, tables. Uses the shared
Google OAuth token."""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "bigquery"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("BigQuery credential missing access_token.")
    return {"Authorization": f"Bearer {token}"}


async def _datasets(client, cred, params, cursor, q):  # noqa: ANN001
    project = (params.get("project_id") or params.get("project") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{project}/datasets",
        headers=_headers(cred),
        params={"maxResults": 100, **({"pageToken": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=d["datasetReference"]["datasetId"], label=d["datasetReference"]["datasetId"])
        for d in payload.get("datasets", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _tables(client, cred, params, cursor, q):  # noqa: ANN001
    project = (params.get("project_id") or "").strip()
    dataset = (params.get("dataset") or params.get("dataset_id") or "").strip()
    if not project or not dataset:
        return LookupResponse(items=[])
    r = await client.get(
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{project}/datasets/{dataset}/tables",
        headers=_headers(cred),
        params={"maxResults": 100, **({"pageToken": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=t["tableReference"]["tableId"],
            label=t["tableReference"]["tableId"],
            sublabel=t.get("type"),
        )
        for t in payload.get("tables", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


LOOKUPS = {"datasets": _datasets, "tables": _tables}
