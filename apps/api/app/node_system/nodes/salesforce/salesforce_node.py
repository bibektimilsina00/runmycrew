"""Salesforce action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.salesforce.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SalesforceNode = build_rest_node(MANIFEST)
