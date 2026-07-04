"""PagerDuty polling trigger — built via the polling scaffold."""

from apps.api.app.node_system.nodes.pagerduty.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

PagerDutyTriggerNode = build_polling_trigger(MANIFEST)
