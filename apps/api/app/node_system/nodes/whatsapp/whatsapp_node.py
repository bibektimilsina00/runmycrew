"""WhatsApp Business action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.whatsapp.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

WhatsAppNode = build_rest_node(MANIFEST)
