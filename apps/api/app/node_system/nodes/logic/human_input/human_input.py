from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class InputField(BaseModel):
    name: str
    label: str = ""
    type: str = "string"  # string | number | boolean | text
    required: bool = False


class HumanInputProperties(BaseModel):
    title: str = "Human Approval Required"
    description: str = ""
    fields: list[InputField] | str = Field(default_factory=list)
    timeoutHours: int = 72
    # Reuses the workspace's Escalation config (Settings → Automations) to
    # ping a human when the pause fires. Empty / off = silent pause.
    notify: bool = False
    notifyMessage: str = ""


class HumanInputNode(BaseNode[HumanInputProperties]):
    @classmethod
    def get_properties_model(cls) -> type[HumanInputProperties]:
        return HumanInputProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.human_input",
            name="Human Input",
            category="logic",
            description="Pause workflow and wait for a human to provide input or approval.",
            icon="UserCheck",
            color="#f59e0b",
            properties=[
                {
                    "name": "title",
                    "label": "Title",
                    "type": "string",
                    "default": "Human Approval Required",
                },
                {
                    "name": "description",
                    "label": "Instructions",
                    "type": "string",
                    "placeholder": "Please review and approve...",
                },
                {
                    "name": "fields",
                    "label": "Input Fields",
                    "type": "json",
                    "default": [
                        {
                            "name": "approved",
                            "label": "Approved?",
                            "type": "boolean",
                            "required": True,
                        }
                    ],
                    "description": "Fields the human must fill. Each: {name, label, type, required}.",
                },
                {
                    "name": "timeoutHours",
                    "label": "Timeout (hours)",
                    "type": "number",
                    "default": 72,
                    "mode": "advanced",
                },
                {
                    "name": "notify",
                    "label": "Notify a human",
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "Send a message via the workspace's escalation handler "
                        "(Slack / webhook / email) so someone knows to review."
                    ),
                },
                {
                    "name": "notifyMessage",
                    "label": "Notification message",
                    "type": "string",
                    "condition": {"field": "notify", "value": True},
                    "placeholder": "A workflow is waiting on your approval.",
                    "description": "Message body sent alongside the resume link.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "input", "type": "object"},
                {"label": "approved", "type": "boolean"},
            ],
            allow_error=True,
        )

    def _parse_fields(self) -> list[InputField]:
        raw = self.props.fields
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return []
        if not isinstance(raw, list):
            return []
        fields = []
        for item in raw:
            if isinstance(item, InputField):
                fields.append(item)
            elif isinstance(item, dict):
                with suppress(Exception):
                    fields.append(InputField(**item))
        return fields

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.pause is None:
            return NodeResult(
                success=False,
                error="Human Input node requires pause/resume support — not available in this context",
            )

        fields = self._parse_fields()
        resume_schema = {
            "title": self.props.title,
            "description": self.props.description,
            "fields": [f.model_dump() for f in fields],
            "timeoutHours": self.props.timeoutHours,
            "context": input_data,
        }

        if self.props.notify:
            await self._notify_human(context)

        # This raises PauseSignal — execution stops here until resumed
        await context.pause(resume_schema)

        # Never reached; resume_input becomes this node's output via _resume_from()
        return NodeResult(success=True, output_data={})

    async def _notify_human(self, context: NodeContext) -> None:
        """Best-effort ping via the workspace escalation handler.

        Never raises: the pause must succeed even when notification
        infra is misconfigured. Uses the same schema as budget-exhausted
        agent escalations so downstream consumers already know the shape.
        """
        try:
            import uuid as _uuid
            from datetime import UTC, datetime

            from apps.api.app.features.escalation.repository import (
                EscalationConfigRepository,
            )
            from apps.api.app.features.escalation.schemas import (
                EscalationConfig,
                EscalationPayload,
            )
            from apps.api.app.features.escalation.service import EscalationService

            if not context.db or not context.workspace_id:
                return
            try:
                ws_uuid = _uuid.UUID(context.workspace_id)
            except (ValueError, TypeError):
                return

            row = await EscalationConfigRepository(context.db).get_for_workspace(ws_uuid)
            if row is None:
                return
            config = EscalationConfig(
                workspace_id=row.workspace_id,
                slack_webhook_url=row.slack_webhook_url,
                email_to=row.email_to,
                webhook_url=row.webhook_url,
                enabled=row.enabled,
            )

            now = datetime.now(UTC)
            message = (
                self.props.notifyMessage
                or f"{self.props.title} — a workflow is paused for approval."
            )
            payload = EscalationPayload(
                workflow_id=_uuid.UUID(context.workflow_id)
                if _isuuid(context.workflow_id)
                else _uuid.uuid4(),
                workflow_name=self.props.title or "Human Input",
                run_id=_uuid.UUID(context.execution_id)
                if _isuuid(context.execution_id)
                else _uuid.uuid4(),
                run_url="",
                status="paused",
                failure_reason=None,
                started_at=now,
                ended_at=now,
                trace_summary=message,
            )
            await EscalationService().dispatch(config, payload)
        except Exception:  # noqa: BLE001 — notification must never break pause
            return


def _isuuid(v: str) -> bool:
    try:
        import uuid as _u

        _u.UUID(v)
        return True
    except (ValueError, TypeError):
        return False
