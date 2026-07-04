"""Gong webhook trigger — built via the webhook scaffold."""

from apps.api.app.node_system.nodes.gong.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

GongWebhookTriggerNode = build_webhook_trigger(MANIFEST)
