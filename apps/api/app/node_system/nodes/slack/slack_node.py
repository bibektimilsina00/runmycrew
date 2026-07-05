"""Slack action node — built via the REST scaffold.

Previously a 628-LOC custom BaseNode routing through SlackService.
Refactored to declarative REST scaffold. All existing op names and
endpoints preserved. `SlackService` stays in
`apps/api/app/integrations/slack/service.py` for use by feature-layer
callers (settings screens, admin flows, oauth exchange).
"""

from apps.api.app.node_system.nodes.slack.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SlackNode = build_rest_node(MANIFEST)
