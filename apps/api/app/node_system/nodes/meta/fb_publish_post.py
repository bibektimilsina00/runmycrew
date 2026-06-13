from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import (
    find_credential,
    page_token_by_page_id,
)


class FBPublishPostProperties(BaseModel):
    credential: str | None = None
    page_id: str = ""
    message: str = ""
    link: str | None = None


class FBPublishPostNode(BaseNode[FBPublishPostProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.fb_publish_post",
            name="Publish Facebook Post",
            category="action",
            description="Publish a text + optional link post to the connected Facebook Page.",
            icon="Megaphone",
            color="#1877F2",
            properties=[
                {
                    "name": "credential",
                    "label": "Meta Account",
                    "type": "credential",
                    "credentialType": "meta_oauth",
                    "required": True,
                },
                {
                    "name": "page_id",
                    "label": "Facebook Page",
                    "type": "meta-resource",
                    "resourceKind": "page",
                    "dependsOn": ["credential"],
                    "required": True,
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                },
                {
                    "name": "link",
                    "label": "Link (optional)",
                    "type": "string",
                    "placeholder": "https://...",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "post_id", "type": "string"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[FBPublishPostProperties]:
        return FBPublishPostProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")
        if not self.props.message.strip():
            return NodeResult(success=False, error="message is required")

        credential = find_credential(context.credentials, self.props.credential)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")
        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")

        token = page_token_by_page_id(data, self.props.page_id)
        if not token:
            return NodeResult(success=False, error="No page access token for this Page.")

        service = MetaService(context.db)
        try:
            resp = await service.fb_publish_post(
                token,
                self.props.page_id,
                self.props.message,
                self.props.link,
            )
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))
        return NodeResult(
            success=True,
            output_data={"post_id": str(resp.get("id") or ""), "response": resp},
        )
