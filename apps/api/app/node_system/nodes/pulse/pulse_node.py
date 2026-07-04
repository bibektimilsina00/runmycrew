"""Pulse action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.pulse.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

PulseNode = build_rest_node(MANIFEST)
