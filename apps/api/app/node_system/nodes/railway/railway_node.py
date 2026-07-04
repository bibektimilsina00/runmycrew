"""Railway action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.railway.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

RailwayNode = build_rest_node(MANIFEST)
