from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.route_to import COLOR, ICON_SLUG, NAME


class RouteToProperties(BaseModel):
    to_persona_id: str | None = None
    to_role: str = ""
    message: str = ""


class RouteToNode(BaseNode[RouteToProperties]):
    """Pass-through router: labels the next agent's persona / role.

    Downstream agent nodes read ``$previous_node.output`` and pick up
    ``to_persona_id`` / ``to_role`` to overlay their own execution.
    """

    @classmethod
    def get_properties_model(cls) -> type[RouteToProperties]:
        return RouteToProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="ai.route_to",
            name=NAME,
            category="ai",
            description=(
                "Explicit A→B message routing. Emits {to_persona_id, to_role, message} "
                "for the next agent node to consume."
            ),
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "to_persona_id",
                    "label": "Route To Persona",
                    "type": "persona-picker",
                    "required": False,
                    "description": "Persona that should handle the next round.",
                },
                {
                    "name": "to_role",
                    "label": "Or Role",
                    "type": "string",
                    "placeholder": "reviewer",
                    "description": "Fallback role tag when no persona is picked.",
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "placeholder": "Please review the writeup and flag issues.",
                    "description": "Message forwarded to the next agent.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "to_persona_id", "type": "string"},
                {"label": "to_role", "type": "string"},
                {"label": "message", "type": "string"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        message = self.props.message or (
            input_data.get("content") if isinstance(input_data.get("content"), str) else ""
        )
        return NodeResult(
            success=True,
            output_data={
                "to_persona_id": self.props.to_persona_id or None,
                "to_role": self.props.to_role or None,
                "message": message or "",
            },
        )
