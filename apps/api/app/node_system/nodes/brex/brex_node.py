"""Brex action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.brex.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

BrexNode = build_rest_node(MANIFEST)
