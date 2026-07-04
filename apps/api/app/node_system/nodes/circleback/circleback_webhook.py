"""Circleback webhook trigger node — built via the webhook trigger scaffold."""

from apps.api.app.node_system.nodes.circleback.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

CirclebackWebhookTriggerNode = build_webhook_trigger(MANIFEST)
