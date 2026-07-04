"""Tinybird action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.tinybird.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

TinybirdNode = build_rest_node(MANIFEST)
