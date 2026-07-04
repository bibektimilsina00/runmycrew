"""Lemlist webhook trigger — built via the webhook scaffold."""

from apps.api.app.node_system.nodes.lemlist.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

LemlistWebhookTriggerNode = build_webhook_trigger(MANIFEST)
