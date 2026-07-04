"""Mistral OCR action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.mistral_parse.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MistralOCRNode = build_rest_node(MANIFEST)
