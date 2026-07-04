"""Greptile action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.greptile.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GreptileNode = build_rest_node(MANIFEST)
