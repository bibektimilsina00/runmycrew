"""Enrow action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.enrow.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

EnrowNode = build_rest_node(MANIFEST)
