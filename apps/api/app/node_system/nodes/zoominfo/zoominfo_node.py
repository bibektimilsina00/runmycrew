"""ZoomInfo action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.zoominfo.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ZoomInfoNode = build_rest_node(MANIFEST)
