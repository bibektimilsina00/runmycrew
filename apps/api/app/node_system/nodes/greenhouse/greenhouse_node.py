"""Greenhouse action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.greenhouse.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GreenhouseNode = build_rest_node(MANIFEST)
