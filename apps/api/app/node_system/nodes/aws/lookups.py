"""AWS remote-picker handlers.

AWS credentials (access-key + secret-key) authorize every service, so
all AWS pickers live at the brand root. Handlers use `boto3` sync
clients wrapped in a thread executor — the API doesn't expose an
async client and we want the picker to feel snappy.

We deliberately keep the surface small (regions, S3 buckets, SQS
queues, DynamoDB tables, RDS clusters, SES identities). Adding more
resources = one function + one entry in LOOKUPS.
"""

from __future__ import annotations

import asyncio
from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "aws"

# Static baseline — AWS has ~35 public regions. Baking them in
# side-steps the "which region do we call to list regions" chicken/
# egg. `EC2.describe_regions` needs a region too.
_REGIONS: list[tuple[str, str]] = [
    ("us-east-1", "US East (N. Virginia)"),
    ("us-east-2", "US East (Ohio)"),
    ("us-west-1", "US West (N. California)"),
    ("us-west-2", "US West (Oregon)"),
    ("af-south-1", "Africa (Cape Town)"),
    ("ap-east-1", "Asia Pacific (Hong Kong)"),
    ("ap-south-1", "Asia Pacific (Mumbai)"),
    ("ap-south-2", "Asia Pacific (Hyderabad)"),
    ("ap-northeast-1", "Asia Pacific (Tokyo)"),
    ("ap-northeast-2", "Asia Pacific (Seoul)"),
    ("ap-northeast-3", "Asia Pacific (Osaka)"),
    ("ap-southeast-1", "Asia Pacific (Singapore)"),
    ("ap-southeast-2", "Asia Pacific (Sydney)"),
    ("ap-southeast-3", "Asia Pacific (Jakarta)"),
    ("ap-southeast-4", "Asia Pacific (Melbourne)"),
    ("ca-central-1", "Canada (Central)"),
    ("eu-central-1", "Europe (Frankfurt)"),
    ("eu-central-2", "Europe (Zurich)"),
    ("eu-west-1", "Europe (Ireland)"),
    ("eu-west-2", "Europe (London)"),
    ("eu-west-3", "Europe (Paris)"),
    ("eu-south-1", "Europe (Milan)"),
    ("eu-south-2", "Europe (Spain)"),
    ("eu-north-1", "Europe (Stockholm)"),
    ("me-south-1", "Middle East (Bahrain)"),
    ("me-central-1", "Middle East (UAE)"),
    ("sa-east-1", "South America (São Paulo)"),
]


def _boto3_client(service: str, cred: dict[str, Any], region: str | None = None):
    """Build a boto3 client from a credential dict. `region` falls back
    to whatever the credential specifies, then to us-east-1."""
    import boto3  # imported lazily so tests don't pay the cost on import

    ak = cred.get("access_key_id") or cred.get("aws_access_key_id")
    sk = cred.get("secret_access_key") or cred.get("aws_secret_access_key")
    st = cred.get("session_token") or cred.get("aws_session_token")
    if not ak or not sk:
        raise ValueError("AWS credential missing access_key_id / secret_access_key.")
    return boto3.client(
        service,
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        aws_session_token=st,
        region_name=region or cred.get("region") or "us-east-1",
    )


async def _run(fn, *args, **kwargs):
    """Push a sync boto3 call onto the default thread executor."""
    return await asyncio.get_running_loop().run_in_executor(None, lambda: fn(*args, **kwargs))


async def _regions(_client, _cred, _params, _cursor, q):  # noqa: ANN001
    items = [LookupItem(id=code, label=name, sublabel=code) for code, name in _REGIONS]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower() or needle in it.id.lower()]
    return LookupResponse(items=items)


async def _s3_buckets(_client, cred, _params, _cursor, q):  # noqa: ANN001
    s3 = _boto3_client("s3", cred)
    payload = await _run(s3.list_buckets)
    items = [
        LookupItem(id=b["Name"], label=b["Name"], sublabel=str(b.get("CreationDate")))
        for b in payload.get("Buckets", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _sqs_queues(_client, cred, params, _cursor, q):  # noqa: ANN001
    region = (params.get("region") or "").strip() or None
    sqs = _boto3_client("sqs", cred, region=region)
    payload = await _run(sqs.list_queues, MaxResults=1000)
    items = [
        LookupItem(id=url, label=url.rsplit("/", 1)[-1], sublabel=url)
        for url in payload.get("QueueUrls", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _dynamodb_tables(_client, cred, params, _cursor, q):  # noqa: ANN001
    region = (params.get("region") or "").strip() or None
    ddb = _boto3_client("dynamodb", cred, region=region)
    payload = await _run(ddb.list_tables, Limit=100)
    items = [LookupItem(id=name, label=name) for name in payload.get("TableNames", [])]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _rds_clusters(_client, cred, params, _cursor, q):  # noqa: ANN001
    region = (params.get("region") or "").strip() or None
    rds = _boto3_client("rds", cred, region=region)
    payload = await _run(rds.describe_db_clusters)
    items = [
        LookupItem(
            id=c["DBClusterIdentifier"],
            label=c["DBClusterIdentifier"],
            sublabel=c.get("Engine"),
        )
        for c in payload.get("DBClusters", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _ses_identities(_client, cred, params, _cursor, q):  # noqa: ANN001
    region = (params.get("region") or "").strip() or None
    ses = _boto3_client("ses", cred, region=region)
    payload = await _run(ses.list_identities, MaxItems=1000)
    items = [LookupItem(id=i, label=i) for i in payload.get("Identities", [])]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {
    "regions": _regions,
    "s3_buckets": _s3_buckets,
    "sqs_queues": _sqs_queues,
    "dynamodb_tables": _dynamodb_tables,
    "rds_clusters": _rds_clusters,
    "ses_identities": _ses_identities,
}
