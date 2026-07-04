"""WhatsApp webhook trigger node — built via the webhook trigger scaffold."""

from apps.api.app.node_system.nodes.whatsapp.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

WhatsAppWebhookTriggerNode = build_webhook_trigger(MANIFEST)
