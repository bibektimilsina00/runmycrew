"""AgentMail action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.agentmail.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AgentMailNode = build_rest_node(MANIFEST)
