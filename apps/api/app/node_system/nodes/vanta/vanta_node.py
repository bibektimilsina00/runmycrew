"""Vanta action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.vanta.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

VantaNode = build_rest_node(MANIFEST)
