"""Luma action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.luma.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LumaNode = build_rest_node(MANIFEST)
