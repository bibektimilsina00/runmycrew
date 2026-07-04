"""Ketch action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.ketch.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

KetchNode = build_rest_node(MANIFEST)
