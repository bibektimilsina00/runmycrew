"""ZeroBounce action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.zerobounce.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ZeroBounceNode = build_rest_node(MANIFEST)
