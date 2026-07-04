"""Ahrefs action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.ahrefs.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AhrefsNode = build_rest_node(MANIFEST)
