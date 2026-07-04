"""Workday action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.workday.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

WorkdayNode = build_rest_node(MANIFEST)
