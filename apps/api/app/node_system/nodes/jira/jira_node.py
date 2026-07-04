"""Jira action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.jira.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

JiraNode = build_rest_node(MANIFEST)
