"""Twilio Voice webhook trigger node — built via the webhook trigger scaffold."""

from apps.api.app.node_system.nodes.twilio.twilio_voice.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

TwilioVoiceWebhookTriggerNode = build_webhook_trigger(MANIFEST)
