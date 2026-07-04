"""Guardrails AI action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.guardrails.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GuardrailsNode = build_rest_node(MANIFEST)
