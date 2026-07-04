"""ClickHouse Cloud action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.clickhouse.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ClickHouseCloudNode = build_rest_node(MANIFEST)
