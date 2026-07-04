"""GitLab polling trigger — built via the polling scaffold."""

from apps.api.app.node_system.nodes.gitlab.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

GitLabTriggerNode = build_polling_trigger(MANIFEST)
