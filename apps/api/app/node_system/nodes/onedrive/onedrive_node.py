"""OneDrive action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.onedrive.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

OneDriveNode = build_rest_node(MANIFEST)
