"""Dagster Cloud action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.dagster.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DagsterCloudNode = build_rest_node(MANIFEST)
