"""Profound action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.profound.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ProfoundNode = build_rest_node(MANIFEST)
