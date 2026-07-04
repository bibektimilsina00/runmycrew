"""Outlook action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.outlook.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

OutlookNode = build_rest_node(MANIFEST)
