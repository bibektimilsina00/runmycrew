"""Daytona action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.daytona.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DaytonaNode = build_rest_node(MANIFEST)
