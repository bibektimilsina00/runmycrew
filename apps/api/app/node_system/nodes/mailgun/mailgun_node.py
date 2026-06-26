"""Mailgun action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.mailgun.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MailgunNode = build_rest_node(MANIFEST)
