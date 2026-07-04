"""Video Generator (Runway/HeyGen) action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.video_generator.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

VideoGeneratorNode = build_rest_node(MANIFEST)
