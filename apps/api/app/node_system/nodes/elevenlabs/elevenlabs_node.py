"""ElevenLabs action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.elevenlabs.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ElevenLabsNode = build_rest_node(MANIFEST)
