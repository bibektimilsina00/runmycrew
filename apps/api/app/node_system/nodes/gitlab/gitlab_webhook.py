"""GitLab webhook trigger node — built from a manifest via the
webhook scaffold. See `webhook_manifest.py` for the per-event +
signature spec."""

from apps.api.app.node_system.nodes.gitlab.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

GitLabWebhookTriggerNode = build_webhook_trigger(MANIFEST)
