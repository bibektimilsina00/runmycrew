"""RB2B action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.rb2b.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

RB2BNode = build_rest_node(MANIFEST)
