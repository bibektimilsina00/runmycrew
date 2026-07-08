"""Twilio SMS action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.twilio.twilio_sms.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

TwilioSMSNode = build_rest_node(MANIFEST)
