from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class FBReactionTriggerProperties(BaseModel):
    page_id: str = ""
    reaction_type: str | None = Field(
        default=None,
        description="Optional filter (LIKE / LOVE / WOW / HAHA / SAD / ANGRY / CARE).",
    )


class FBReactionTriggerNode(BaseNode[FBReactionTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.fb_reaction",
            name="Facebook Post Reaction",
            category="trigger",
            description=(
                "Fires when a user reacts to a post by the connected Facebook "
                "Page. Optionally filter by reaction type."
            ),
            icon="Heart",
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
                    "name": "reaction_type",
                    "label": "Reaction filter (optional)",
                    "type": "options",
                    "default": None,
                    "options": [
                        {"label": "Any", "value": None},
                        {"label": "Like", "value": "like"},
                        {"label": "Love", "value": "love"},
                        {"label": "Wow", "value": "wow"},
                        {"label": "Haha", "value": "haha"},
                        {"label": "Sad", "value": "sad"},
                        {"label": "Angry", "value": "angry"},
                        {"label": "Care", "value": "care"},
                    ],
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "post_id", "type": "string"},
                {"label": "user_id", "type": "string"},
                {"label": "reaction_type", "type": "string"},
                {"label": "verb", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[FBReactionTriggerProperties]:
        return FBReactionTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        from_field = value.get("from") or {}
        reaction = str(value.get("reaction_type") or "").lower()

        wanted = (self.props.reaction_type or "").strip().lower()
        if wanted and wanted != reaction:
            return NodeResult(success=True, output_data={"skipped": "reaction mismatch"})

        return NodeResult(
            success=True,
            output_data={
                "post_id": str(value.get("post_id") or ""),
                "user_id": str(from_field.get("id") or ""),
                "reaction_type": reaction,
                "verb": str(value.get("verb") or ""),
                "received_at": str(input_data.get("received_at") or ""),
                "payload": value,
            },
        )
