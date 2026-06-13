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
    page_token_by_ig_account_id,
)


class IGPublishStoryProperties(BaseModel):
    credential: str | None = None
    ig_account_id: str = ""
    media_url: str = ""  # public URL of the image / video


class IGPublishStoryNode(BaseNode[IGPublishStoryProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.ig_publish_story",
            name="Publish Instagram Story",
            category="action",
            description=(
                "Publish an image or video to the connected Instagram "
                "Business account's story. Captions, links, stickers, and "
                "polls are not supported via the API (Meta restriction)."
            ),
            icon="Circle",
            color="#E1306C",
            properties=[
                {
                    "name": "credential",
                    "label": "Meta Account",
                    "type": "credential",
                    "credentialType": "meta_oauth",
                    "required": True,
                },
                {
                    "name": "ig_account_id",
                    "label": "Instagram Account",
                    "type": "meta-resource",
                    "resourceKind": "ig_account",
                    "dependsOn": ["credential"],
                    "required": True,
                },
                {
                    "name": "media_url",
                    "label": "Public Media URL",
                    "type": "string",
                    "required": True,
                    "placeholder": "https://...",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "media_id", "type": "string"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[IGPublishStoryProperties]:
        return IGPublishStoryProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")
        if not self.props.media_url.strip():
            return NodeResult(success=False, error="media_url is required")

        credential = find_credential(context.credentials, self.props.credential)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")
        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")

        token = page_token_by_ig_account_id(data, self.props.ig_account_id)
        if not token:
            return NodeResult(
                success=False,
                error="No page access token for this Instagram account.",
            )

        service = MetaService(context.db)
        try:
            resp = await service.ig_publish_media(
                page_access_token=token,
                ig_user_id=self.props.ig_account_id,
                media_url=self.props.media_url,
                kind="STORIES",
            )
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))
        return NodeResult(
            success=True,
            output_data={"media_id": str(resp.get("id") or ""), "response": resp},
        )
