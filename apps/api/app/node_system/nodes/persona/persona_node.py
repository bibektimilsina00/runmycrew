"""Persona action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.persona.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

PersonaNode = build_rest_node(MANIFEST)
