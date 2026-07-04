"""Bright Data action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.brightdata.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

BrightDataNode = build_rest_node(MANIFEST)
