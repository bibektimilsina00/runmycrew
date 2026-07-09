from __future__ import annotations

import json
import uuid
from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.subcrew import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)


class SubCrewProperties(BaseModel):
    crew_id: str = ""
    input_data: Any = None


class SubCrewNode(BaseNode[SubCrewProperties]):
    """Run another crew inline and use its output as this node's output.

    Loads the target crew's graph and runs it via ``WorkflowRunner`` in
    the current process so the caller can consume the sub-crew's output
    the same way it consumes any other node. Shares credentials +
    emitter with the parent so tokens/costs still stream to the same UI.
    """

    @classmethod
    def get_properties_model(cls) -> type[SubCrewProperties]:
        return SubCrewProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="ai.subcrew",
            name=NAME,
            category="ai",
            description=(
                "Compose crews. Run another crew as a step in this one — its "
                "final output flows into the next node."
            ),
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "crew_id",
                    "label": "Crew ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "UUID of the crew to call",
                    "description": "The ID of the crew to run. Find it in the crew editor URL.",
                },
                {
                    "name": "input_data",
                    "label": "Extra Input (JSON)",
                    "type": "json",
                    "required": False,
                    "description": (
                        "Optional extra fields merged into the trigger data passed to the sub-crew."
                    ),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "sub_crew_output", "type": "object"},
                {"label": "crew_id", "type": "string"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        crew_id_str = (self.props.crew_id or "").strip()
        if not crew_id_str:
            return NodeResult(success=False, error="crew_id is required")
        try:
            crew_uuid = uuid.UUID(crew_id_str)
        except ValueError:
            return NodeResult(success=False, error=f"Invalid crew_id: {crew_id_str!r}")

        extra = self.props.input_data or {}
        if isinstance(extra, str):
            try:
                extra = json.loads(extra)
            except Exception:
                extra = {}

        try:
            from apps.api.app.core.database import AsyncSessionLocal
            from apps.api.app.execution_engine.engine.workflow_runner import (
                WorkflowRunner,
            )
            from apps.api.app.features.crews.repository import CrewRepository

            async with AsyncSessionLocal() as db:
                repo = CrewRepository(db)
                crew = await repo.get_by_id(crew_uuid)
                if not crew:
                    return NodeResult(success=False, error=f"Crew {crew_id_str} not found")

                sub_input = {**input_data, **extra}
                sub_execution_id = f"{context.execution_id}-subcrew-{crew_id_str[:8]}"

                runner = WorkflowRunner(
                    workflow_id=str(crew.id),
                    execution_id=sub_execution_id,
                    graph=crew.graph,
                    db=db,
                    credentials=context.credentials,
                    emitter=context.emitter,
                )
                output = await runner.run(sub_input)

            return NodeResult(
                success=True,
                output_data={"sub_crew_output": output, "crew_id": crew_id_str},
            )
        except Exception as e:
            logger.error(f"SubCrewNode failed for crew {crew_id_str}: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
