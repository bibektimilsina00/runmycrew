"""LinQ action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.linq.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LinqNode = build_rest_node(MANIFEST)
