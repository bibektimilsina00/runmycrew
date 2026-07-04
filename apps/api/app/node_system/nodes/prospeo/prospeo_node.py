"""Prospeo action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.prospeo.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ProspeoNode = build_rest_node(MANIFEST)
