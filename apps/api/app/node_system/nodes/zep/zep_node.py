"""Zep action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.zep.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ZepNode = build_rest_node(MANIFEST)
