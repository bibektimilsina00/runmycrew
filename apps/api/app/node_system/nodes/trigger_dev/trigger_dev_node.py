"""Trigger.dev action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.trigger_dev.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

TriggerDevNode = build_rest_node(MANIFEST)
