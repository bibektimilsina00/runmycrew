"""SharePoint action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.microsoft.sharepoint.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SharePointNode = build_rest_node(MANIFEST)
