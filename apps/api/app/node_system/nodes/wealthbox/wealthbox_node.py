"""Wealthbox action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.wealthbox.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

WealthboxNode = build_rest_node(MANIFEST)
