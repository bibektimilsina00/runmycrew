"""OpenAI action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.openai.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

OpenAINode = build_rest_node(MANIFEST)
