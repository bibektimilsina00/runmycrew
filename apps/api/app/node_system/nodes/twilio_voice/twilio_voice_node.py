"""Twilio Voice action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.twilio_voice.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

TwilioVoiceNode = build_rest_node(MANIFEST)
