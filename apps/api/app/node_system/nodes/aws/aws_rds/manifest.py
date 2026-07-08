"""AWS RDS action node — manifest form.

Query protocol at `https://rds.{region}.amazonaws.com/`. Version
`2014-10-31`. Describe + create + delete DB instances, snapshots,
clusters. Read-heavy workflow — most workflow use is inspecting
existing DBs, not provisioning.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://rds.{region}.amazonaws.com/"
_VERSION = "2014-10-31"


def _q(action: str, **params) -> dict:
    return {
        "Action": action,
        "Version": _VERSION,
        **{k: v for k, v in params.items() if v is not None},
    }


MANIFEST = ProviderManifest(
    type="action.aws_rds",
    name="AWS RDS",
    category="integration",
    description="AWS RDS — describe DB instances, snapshots, clusters.",
    icon_slug="aws-rds",
    color="#ffffff",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="rds",
    aws_default_region="us-east-1",
    content_type="application/x-www-form-urlencoded",
    fields=[
        FieldSpec(name="db_instance_id", label="DB Instance ID", type="string"),
        FieldSpec(name="db_cluster_id", label="DB Cluster ID", type="string"),
        FieldSpec(name="snapshot_id", label="Snapshot ID", type="string"),
        FieldSpec(
            name="engine",
            label="Engine",
            type="string",
            placeholder="postgres | mysql | aurora-postgresql",
        ),
        FieldSpec(
            name="instance_class", label="Instance Class", type="string", placeholder="db.t3.micro"
        ),
        FieldSpec(
            name="storage_gb", label="Allocated Storage (GB)", type="number", mode="advanced"
        ),
        FieldSpec(name="master_username", label="Master Username", type="string", mode="advanced"),
        FieldSpec(
            name="master_password",
            label="Master Password",
            type="string",
            secret=True,
            mode="advanced",
        ),
        FieldSpec(
            name="max_records", label="Max Records", type="number", default=100, mode="advanced"
        ),
        FieldSpec(name="marker", label="Marker (pagination)", type="string", mode="advanced"),
        FieldSpec(
            name="skip_final_snapshot",
            label="Skip final snapshot on delete",
            type="boolean",
            default=True,
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="describe_db_instances",
            label="Describe DB Instances",
            method="POST",
            path=_HOST,
            visible_fields=["db_instance_id", "max_records", "marker"],
            body_builder=lambda v: _q(
                "DescribeDBInstances",
                DBInstanceIdentifier=getattr(v, "db_instance_id", None),
                MaxRecords=int(getattr(v, "max_records", 100) or 100),
                Marker=getattr(v, "marker", None),
            ),
        ),
        OpSpec(
            id="describe_db_clusters",
            label="Describe DB Clusters",
            method="POST",
            path=_HOST,
            visible_fields=["db_cluster_id", "max_records"],
            body_builder=lambda v: _q(
                "DescribeDBClusters",
                DBClusterIdentifier=getattr(v, "db_cluster_id", None),
                MaxRecords=int(getattr(v, "max_records", 100) or 100),
            ),
        ),
        OpSpec(
            id="describe_db_snapshots",
            label="Describe DB Snapshots",
            method="POST",
            path=_HOST,
            visible_fields=["db_instance_id", "snapshot_id"],
            body_builder=lambda v: _q(
                "DescribeDBSnapshots",
                DBInstanceIdentifier=getattr(v, "db_instance_id", None),
                DBSnapshotIdentifier=getattr(v, "snapshot_id", None),
            ),
        ),
        OpSpec(
            id="create_db_snapshot",
            label="Create DB Snapshot",
            method="POST",
            path=_HOST,
            visible_fields=["db_instance_id", "snapshot_id"],
            body_builder=lambda v: _q(
                "CreateDBSnapshot",
                DBInstanceIdentifier=getattr(v, "db_instance_id", None) or "",
                DBSnapshotIdentifier=getattr(v, "snapshot_id", None) or "",
            ),
        ),
        OpSpec(
            id="delete_db_snapshot",
            label="Delete DB Snapshot",
            method="POST",
            path=_HOST,
            visible_fields=["snapshot_id"],
            body_builder=lambda v: _q(
                "DeleteDBSnapshot",
                DBSnapshotIdentifier=getattr(v, "snapshot_id", None) or "",
            ),
            success_payload_template={"deleted": True, "snapshot_id": "{snapshot_id}"},
        ),
        OpSpec(
            id="create_db_instance",
            label="Create DB Instance",
            method="POST",
            path=_HOST,
            visible_fields=[
                "db_instance_id",
                "engine",
                "instance_class",
                "storage_gb",
                "master_username",
                "master_password",
            ],
            body_builder=lambda v: _q(
                "CreateDBInstance",
                DBInstanceIdentifier=getattr(v, "db_instance_id", None) or "",
                Engine=getattr(v, "engine", None) or "postgres",
                DBInstanceClass=getattr(v, "instance_class", None) or "db.t3.micro",
                AllocatedStorage=int(getattr(v, "storage_gb", 20) or 20),
                MasterUsername=getattr(v, "master_username", None),
                MasterUserPassword=getattr(v, "master_password", None),
            ),
        ),
        OpSpec(
            id="delete_db_instance",
            label="Delete DB Instance",
            method="POST",
            path=_HOST,
            visible_fields=["db_instance_id", "skip_final_snapshot"],
            body_builder=lambda v: _q(
                "DeleteDBInstance",
                DBInstanceIdentifier=getattr(v, "db_instance_id", None) or "",
                SkipFinalSnapshot=bool(getattr(v, "skip_final_snapshot", True)),
            ),
        ),
        OpSpec(
            id="reboot_db_instance",
            label="Reboot DB Instance",
            method="POST",
            path=_HOST,
            visible_fields=["db_instance_id"],
            body_builder=lambda v: _q(
                "RebootDBInstance",
                DBInstanceIdentifier=getattr(v, "db_instance_id", None) or "",
            ),
        ),
    ],
    outputs_schema=[
        {"label": "DescribeDBInstancesResult", "type": "object"},
        {"label": "DBInstances", "type": "array"},
        {"label": "DBClusters", "type": "array"},
        {"label": "DBSnapshots", "type": "array"},
        {"label": "ResponseMetadata", "type": "object"},
    ],
    allow_error=True,
)
