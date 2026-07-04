"""AgentPhone action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.agentphone.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AgentPhoneNode = build_rest_node(MANIFEST)
