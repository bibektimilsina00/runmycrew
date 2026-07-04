"""ServiceNow polling trigger — built via the polling scaffold."""

from apps.api.app.node_system.nodes.servicenow.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

ServiceNowTriggerNode = build_polling_trigger(MANIFEST)
