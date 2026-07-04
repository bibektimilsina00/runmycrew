"""Temporal Cloud action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.temporal.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

TemporalCloudNode = build_rest_node(MANIFEST)
