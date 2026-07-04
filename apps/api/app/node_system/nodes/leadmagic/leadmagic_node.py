"""LeadMagic action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.leadmagic.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LeadMagicNode = build_rest_node(MANIFEST)
