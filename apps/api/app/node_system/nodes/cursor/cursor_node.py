"""Cursor action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.cursor.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

CursorNode = build_rest_node(MANIFEST)
