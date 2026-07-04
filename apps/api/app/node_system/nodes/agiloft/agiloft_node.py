"""Agiloft action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.agiloft.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AgiloftNode = build_rest_node(MANIFEST)
