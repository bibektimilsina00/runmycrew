"""GitHub webhook trigger — instant delivery via repo webhook + HMAC verify.

Setup
  1. Add this trigger to your workflow.
  2. Open the repo on GitHub → Settings → Webhooks → Add webhook.
  3. Payload URL: `${BASE_URL}/api/v1/webhooks/github/${workflow_id}` —
     the inspector description shows the resolved value.
  4. Content type: `application/json`.
  5. Secret: paste the value from this node's `secret` field.
  6. Pick the events that match this node's `event` selector (or "Send me
     everything" + filter here).

Verification uses GitHub's `X-Hub-Signature-256` — same HMAC-SHA256 scheme
that powers the rest of the integration. Requests without a valid signature
are rejected at the router layer.

Event filter
  GitHub posts every subscribed event to the same URL. This node carries
  an `event` dropdown that the receiver service uses to short-circuit
  irrelevant deliveries before they dispatch a workflow execution.
  Pick "Any event" to forward everything.

Polling alternative: `github_trigger.py` for environments where a public
webhook URL isn't an option (firewalled installs, ephemeral previews).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

# Subset of GitHub webhook events that workflows commonly route on.
# Mirror GitHub's exact event names so the X-GitHub-Event header drops
# in unchanged. Add more as customers ask for them.
EVENT_ANY = "*"
EVENT_OPTIONS: list[dict[str, str]] = [
    {"label": "Any event", "value": EVENT_ANY},
    {"label": "Issues (issues)", "value": "issues"},
    {"label": "Issue comment (issue_comment)", "value": "issue_comment"},
    {"label": "Pull request (pull_request)", "value": "pull_request"},
    {"label": "Pull request review (pull_request_review)", "value": "pull_request_review"},
    {
        "label": "Pull request review comment (pull_request_review_comment)",
        "value": "pull_request_review_comment",
    },
    {"label": "Push (push)", "value": "push"},
    {"label": "Release (release)", "value": "release"},
    {"label": "Star (star)", "value": "star"},
    {"label": "Fork (fork)", "value": "fork"},
    {"label": "Workflow run (workflow_run)", "value": "workflow_run"},
    {"label": "Discussion (discussion)", "value": "discussion"},
    {"label": "Deployment (deployment)", "value": "deployment"},
    {"label": "Check run (check_run)", "value": "check_run"},
]


class GitHubWebhookTriggerProperties(BaseModel):
    # Credential is optional — webhooks don't need an OAuth token to
    # receive deliveries. We keep the field so users can run companion
    # API calls (e.g. fetch issue body) from the same node context if
    # they later want to enrich the payload.
    credential: str | None = None
    owner: str = ""
    repo: str = ""
    event: str = EVENT_ANY
    secret: str = ""

    @field_validator("owner", "repo", mode="before")
    @classmethod
    def _coerce_picker(cls, value: Any) -> str:
        if isinstance(value, dict):
            v = value.get("name") or value.get("value") or value.get("id")
            return str(v) if isinstance(v, str) else ""
        return str(value or "")


class GitHubWebhookTriggerNode(BaseNode[GitHubWebhookTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GitHubWebhookTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.github_webhook",
            name="GitHub",
            category="trigger",
            description=(
                "Fires the instant GitHub posts a webhook delivery to your "
                "workflow URL. Pair with a repo-level webhook configured "
                "in GitHub Settings → Webhooks. Use the polling GitHub "
                "trigger if you can't expose a public URL."
            ),
            icon="github",
            color="#ffffff",
            credential_type=["github_oauth", "github_pat"],
            properties=[
                {
                    "name": "credential",
                    "label": "GitHub Account (optional)",
                    "type": "credential",
                    "credentialType": ["github_oauth", "github_pat"],
                    "required": False,
                    "description": (
                        "Optional — only needed if downstream nodes call "
                        "GitHub APIs on the same flow."
                    ),
                },
                {
                    "name": "owner",
                    "label": "Owner (user or org)",
                    "type": "string",
                    "required": True,
                    "placeholder": "octocat",
                    "description": "Only used as a label / sanity check; the URL is what GitHub posts to.",
                },
                {
                    "name": "repo",
                    "label": "Repository",
                    "type": "string",
                    "required": True,
                    "placeholder": "hello-world",
                    "loadOptions": "/integrations/github/repos",
                    "loadOptionsDependsOn": ["credential", "owner"],
                },
                {
                    "name": "event",
                    "label": "Event",
                    "type": "options",
                    "default": EVENT_ANY,
                    "options": EVENT_OPTIONS,
                    "description": (
                        "Filter applied to GitHub's `X-GitHub-Event` header. "
                        'Pick "Any event" to forward every delivery.'
                    ),
                },
                {
                    "name": "secret",
                    "label": "Webhook Secret",
                    "type": "string",
                    "secret": True,
                    "required": True,
                    "placeholder": "Set the same value in GitHub → Webhook → Secret",
                    "description": (
                        "HMAC-SHA256 secret. Deliveries without a matching "
                        "`X-Hub-Signature-256` header are rejected."
                    ),
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "event", "type": "string"},
                {"label": "delivery", "type": "string"},
                {"label": "action", "type": "string"},
                {"label": "repository", "type": "string"},
                {"label": "sender", "type": "string"},
                {"label": "body", "type": "object"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Receiver dispatches with the payload already shaped; pass it
        # through so downstream nodes see what `/listen` returned.
        return NodeResult(success=True, output_data=input_data or {})
