"""Datadog action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.datadog.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DatadogNode = build_rest_node(MANIFEST)
