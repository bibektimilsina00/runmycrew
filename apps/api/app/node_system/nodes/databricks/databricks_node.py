"""Databricks action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.databricks.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DatabricksNode = build_rest_node(MANIFEST)
