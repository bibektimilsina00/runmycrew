"""Postmark webhook trigger — built via the webhook scaffold."""

from apps.api.app.node_system.nodes.postmark.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

PostmarkWebhookTriggerNode = build_webhook_trigger(MANIFEST)
