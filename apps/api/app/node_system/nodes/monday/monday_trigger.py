"""Monday.com polling trigger — built via the polling scaffold."""

from apps.api.app.node_system.nodes.monday.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

MondayTriggerNode = build_polling_trigger(MANIFEST)
