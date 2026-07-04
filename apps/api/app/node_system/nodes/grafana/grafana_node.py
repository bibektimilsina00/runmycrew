"""Grafana Cloud action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.grafana.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GrafanaCloudNode = build_rest_node(MANIFEST)
