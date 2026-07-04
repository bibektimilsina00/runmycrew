"""Image Generator (OpenAI DALL-E) action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.image_generator.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ImageGeneratorNode = build_rest_node(MANIFEST)
