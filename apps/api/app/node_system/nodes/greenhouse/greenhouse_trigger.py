"""Greenhouse polling trigger — built via the polling scaffold."""

from apps.api.app.node_system.nodes.greenhouse.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

GreenhouseTriggerNode = build_polling_trigger(MANIFEST)
