"""SixtyFour action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.sixtyfour.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SixtyFourNode = build_rest_node(MANIFEST)
