"""Intercom action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.intercom.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

IntercomNode = build_rest_node(MANIFEST)
