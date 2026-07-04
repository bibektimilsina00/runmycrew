"""Hex action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.hex.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

HexNode = build_rest_node(MANIFEST)
