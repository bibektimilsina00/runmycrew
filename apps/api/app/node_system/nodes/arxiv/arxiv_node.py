"""arXiv action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.arxiv.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ArxivNode = build_rest_node(MANIFEST)
