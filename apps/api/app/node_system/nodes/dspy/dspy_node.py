"""DSPy Cloud action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.dspy.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DSPyCloudNode = build_rest_node(MANIFEST)
