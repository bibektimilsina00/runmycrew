"""LangSmith action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.langsmith.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LangSmithNode = build_rest_node(MANIFEST)
