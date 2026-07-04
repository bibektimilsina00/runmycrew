"""Rippling action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.rippling.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

RipplingNode = build_rest_node(MANIFEST)
