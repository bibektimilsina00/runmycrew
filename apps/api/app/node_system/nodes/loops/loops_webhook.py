"""Loops webhook trigger — built via the webhook scaffold."""

from apps.api.app.node_system.nodes.loops.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

LoopsWebhookTriggerNode = build_webhook_trigger(MANIFEST)
