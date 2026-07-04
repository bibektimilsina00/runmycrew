"""SportMonks action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.sportmonks.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SportMonksNode = build_rest_node(MANIFEST)
