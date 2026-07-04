"""Linkup action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.linkup.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LinkupNode = build_rest_node(MANIFEST)
