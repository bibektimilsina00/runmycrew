"""Linear node — built from a manifest via the REST scaffold.

Same op set + output shape as the previous hand-written class. All op
bodies (GraphQL) moved into `manifest.py` as `CustomHandler`s; the
scaffold handles prop validation, credential injection, and error
framing.
"""

from apps.api.app.node_system.nodes.linear.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LinearNode = build_rest_node(MANIFEST)
