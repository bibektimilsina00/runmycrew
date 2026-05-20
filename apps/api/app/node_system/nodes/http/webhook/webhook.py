from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class WebhookTriggerProperties(BaseModel):
    path: str = ""
    require_signature: bool = False
    secret: str | None = None


class WebhookTriggerNode(BaseNode[WebhookTriggerProperties]):
    @classmethod
    def get_properties_model(cls) -> type[WebhookTriggerProperties]:
        return WebhookTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.webhook",
            name="Webhook Trigger",
            category="trigger",
            description="Trigger workflow via HTTP POST request",
            icon="Zap",
            color="#ec4899",
            properties=[
                {
                    "name": "path",
                    "label": "Webhook Path",
                    "type": "string",
                    "required": True,
                    "placeholder": "my-webhook",
                    "description": "Unique path. Webhook URL: /api/v1/webhooks/{path}",
                },
                {
                    "name": "require_signature",
                    "label": "Require Signature",
                    "type": "boolean",
                    "default": False,
                    "description": "Reject requests without a valid X-Fuse-Signature header",
                },
                {
                    "name": "secret",
                    "label": "Signing Secret",
                    "type": "string",
                    "secret": True,
                    "placeholder": "Click generate to create a secret",
                    "mode": "advanced",
                    "condition": {"field": "require_signature", "value": True},
                    "description": "HMAC-SHA256 secret. Sign with: sha256=HMAC(secret, raw_body)",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "body", "type": "object"},
                {"label": "headers", "type": "object"},
                {"label": "query", "type": "object"},
                {"label": "method", "type": "string"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        return NodeResult(success=True, output_data=input_data)
