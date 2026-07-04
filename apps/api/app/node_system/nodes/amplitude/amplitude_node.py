"""Amplitude action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.amplitude.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AmplitudeNode = build_rest_node(MANIFEST)
