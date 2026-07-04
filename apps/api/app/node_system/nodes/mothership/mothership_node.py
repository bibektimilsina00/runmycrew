"""Mothership action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.mothership.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MothershipNode = build_rest_node(MANIFEST)
