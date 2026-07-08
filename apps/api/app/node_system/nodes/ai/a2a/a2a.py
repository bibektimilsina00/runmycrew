from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.a2a import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)

_POLL_INTERVAL = 2.0  # seconds between status polls


class A2AProperties(BaseModel):
    operation: str = "send_message"  # send_message | get_status | cancel
    targetUrl: str = ""
    message: str = ""
    inputData: Any = None
    authToken: str = ""
    taskId: str = ""  # for get_status / cancel
    waitForCompletion: bool = True  # poll until execution finishes
    timeoutSeconds: int = 120


class A2ANode(BaseNode[A2AProperties]):
    @classmethod
    def get_properties_model(cls) -> type[A2AProperties]:
        return A2AProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.a2a",
            name=NAME,
            category="ai",
            description="Call, check or cancel another agent or workflow via the A2A protocol.",
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "send_message",
                    "options": [
                        {"label": "Send Message", "value": "send_message"},
                        {"label": "Get Status", "value": "get_status"},
                        {"label": "Cancel", "value": "cancel"},
                    ],
                },
                {
                    "name": "targetUrl",
                    "label": "Target URL",
                    "type": "string",
                    "required": True,
                    "placeholder": "https://your-app.com/api/v1/a2a/workflow-id",
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "placeholder": "{{$trigger.output.message}}",
                    "condition": {"field": "operation", "value": "send_message"},
                },
                {
                    "name": "inputData",
                    "label": "Input Data",
                    "type": "json",
                    "required": False,
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "send_message"},
                },
                {
                    "name": "waitForCompletion",
                    "label": "Wait for completion",
                    "type": "boolean",
                    "default": True,
                    "mode": "advanced",
                    "description": "Poll until the remote execution finishes.",
                    "condition": {"field": "operation", "value": "send_message"},
                },
                {
                    "name": "taskId",
                    "label": "Task / Execution ID",
                    "type": "string",
                    "placeholder": "{{$previous.output.executionId}}",
                    "condition": {"field": "operation", "value": "get_status"},
                },
                {
                    "name": "taskId",
                    "label": "Task / Execution ID",
                    "type": "string",
                    "condition": {"field": "operation", "value": "cancel"},
                },
                {
                    "name": "authToken",
                    "label": "Auth Token",
                    "type": "string",
                    "required": False,
                    "mode": "advanced",
                },
                {
                    "name": "timeoutSeconds",
                    "label": "Timeout (seconds)",
                    "type": "number",
                    "default": 120,
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "output", "type": "object"},
                {"label": "status", "type": "string"},
                {"label": "executionId", "type": "string"},
            ],
            allow_error=True,
        )

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        token = self.props.authToken.strip()
        if token:
            h["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"
        return h

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        url = self.props.targetUrl.strip()
        if not url:
            return NodeResult(success=False, error="targetUrl is required")

        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=self.props.timeoutSeconds) as client:
                if op == "send_message":
                    return await self._send_message(client, url, input_data)
                elif op == "get_status":
                    return await self._get_status(client, url)
                elif op == "cancel":
                    return await self._cancel(client, url)
                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")
        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"A2A HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
        except httpx.TimeoutException:
            return NodeResult(
                success=False, error=f"A2A timed out after {self.props.timeoutSeconds}s"
            )
        except Exception as e:
            return NodeResult(success=False, error=f"A2A error: {e}")

    async def _send_message(
        self, client: httpx.AsyncClient, url: str, input_data: dict[str, Any]
    ) -> NodeResult:
        payload: dict[str, Any] = {"message": self.props.message, "trigger_data": input_data}
        if self.props.inputData is not None:
            raw = self.props.inputData
            if isinstance(raw, str):
                with suppress(json.JSONDecodeError):
                    raw = json.loads(raw)
            payload["input_data"] = raw

        resp = await client.post(url, headers=self._headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()
        execution_id = data.get("execution_id", "")

        if not self.props.waitForCompletion or not execution_id:
            return NodeResult(
                success=True,
                output_data={
                    "output": data.get("output"),
                    "status": data.get("status", "running"),
                    "executionId": execution_id,
                },
            )

        # Poll for completion
        status_url = url.rstrip("/") + f"/status/{execution_id}"
        deadline = asyncio.get_event_loop().time() + self.props.timeoutSeconds
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(_POLL_INTERVAL)
            try:
                status_resp = await client.get(status_url, headers=self._headers())
                status_resp.raise_for_status()
                status_data = status_resp.json()
                status = status_data.get("status", "running")
                if status in ("completed", "failed"):
                    return NodeResult(
                        success=status == "completed",
                        output_data={
                            "output": status_data.get("output", {}),
                            "status": status,
                            "executionId": execution_id,
                        },
                        error=status_data.get("error") if status == "failed" else None,
                    )
            except Exception:
                pass  # transient poll failure — keep trying

        return NodeResult(
            success=False, error=f"A2A timed out waiting for execution {execution_id}"
        )

    async def _get_status(self, client: httpx.AsyncClient, url: str) -> NodeResult:
        task_id = self.props.taskId.strip()
        if not task_id:
            return NodeResult(success=False, error="taskId is required for get_status")
        status_url = url.rstrip("/") + f"/status/{task_id}"
        resp = await client.get(status_url, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        return NodeResult(
            success=True,
            output_data={
                "output": data.get("output", {}),
                "status": data.get("status", "unknown"),
                "executionId": task_id,
            },
        )

    async def _cancel(self, client: httpx.AsyncClient, url: str) -> NodeResult:
        task_id = self.props.taskId.strip()
        if not task_id:
            return NodeResult(success=False, error="taskId is required for cancel")
        cancel_url = url.rstrip("/") + f"/{task_id}"
        resp = await client.delete(cancel_url, headers=self._headers())
        resp.raise_for_status()
        return NodeResult(
            success=True,
            output_data={
                "output": {},
                "status": "cancelled",
                "executionId": task_id,
            },
        )
