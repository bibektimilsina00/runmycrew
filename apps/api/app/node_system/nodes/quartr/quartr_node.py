"""Quartr action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.quartr.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

QuartrNode = build_rest_node(MANIFEST)
