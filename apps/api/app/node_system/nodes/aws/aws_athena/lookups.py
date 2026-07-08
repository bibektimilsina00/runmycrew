"""AWS Athena remote-picker handlers — databases, tables, workgroups."""

from __future__ import annotations

import asyncio

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "athena"


def _client(service, cred, region):
    import boto3

    ak = cred.get("access_key_id") or cred.get("aws_access_key_id")
    sk = cred.get("secret_access_key") or cred.get("aws_secret_access_key")
    if not ak or not sk:
        raise ValueError("AWS credential missing access_key_id / secret_access_key.")
    return boto3.client(
        service,
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        aws_session_token=cred.get("session_token"),
        region_name=region or cred.get("region") or "us-east-1",
    )


async def _run(fn, *args, **kwargs):
    return await asyncio.get_running_loop().run_in_executor(None, lambda: fn(*args, **kwargs))


async def _databases(_client_arg, cred, params, _cursor, q):  # noqa: ANN001
    region = (params.get("region") or "").strip() or None
    catalog = (params.get("catalog") or "AwsDataCatalog").strip()
    athena = _client("athena", cred, region)
    payload = await _run(athena.list_databases, CatalogName=catalog, MaxResults=50)
    items = [
        LookupItem(id=db["Name"], label=db["Name"], sublabel=db.get("Description"))
        for db in payload.get("DatabaseList", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _tables(_client_arg, cred, params, _cursor, q):  # noqa: ANN001
    region = (params.get("region") or "").strip() or None
    catalog = (params.get("catalog") or "AwsDataCatalog").strip()
    db = (params.get("database") or "").strip()
    if not db:
        return LookupResponse(items=[])
    athena = _client("athena", cred, region)
    payload = await _run(
        athena.list_table_metadata,
        CatalogName=catalog,
        DatabaseName=db,
        MaxResults=50,
    )
    items = [
        LookupItem(id=t["Name"], label=t["Name"], sublabel=t.get("TableType"))
        for t in payload.get("TableMetadataList", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _workgroups(_client_arg, cred, params, _cursor, q):  # noqa: ANN001
    region = (params.get("region") or "").strip() or None
    athena = _client("athena", cred, region)
    payload = await _run(athena.list_work_groups, MaxResults=50)
    items = [
        LookupItem(id=w["Name"], label=w["Name"], sublabel=w.get("State"))
        for w in payload.get("WorkGroups", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"databases": _databases, "tables": _tables, "workgroups": _workgroups}
