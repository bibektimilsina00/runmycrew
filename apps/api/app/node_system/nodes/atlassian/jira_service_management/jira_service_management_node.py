"""Jira Service Management action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.atlassian.jira_service_management.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

JiraServiceManagementNode = build_rest_node(MANIFEST)
