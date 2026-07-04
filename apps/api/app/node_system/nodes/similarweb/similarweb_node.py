"""SimilarWeb action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.similarweb.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SimilarWebNode = build_rest_node(MANIFEST)
