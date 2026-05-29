from __future__ import annotations

import asyncio
from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

BROWSER_USE_BASE = "https://api.browser-use.com/api/v2"
POLL_INTERVAL = 5.0  # seconds between status checks
MAX_WAIT = 300.0  # 5 minute timeout
TERMINAL_STATES = {"finished", "failed", "stopped"}


class BrowserUseProperties(BaseModel):
    credential: str | None = None
    task: str = ""
    start_url: str | None = None
    model: str = "claude-sonnet-4-5"
    max_steps: int = 50
    allowed_domains: str | None = None
    secrets: Any | None = None  # JSON key-value pairs for injecting into browser
    structured_output: str | None = None  # JSON schema string for structured response
    system_prompt_extension: str | None = None
    vision: bool = True
    flash_mode: bool = False


class BrowserUseNode(BaseNode[BrowserUseProperties]):
    @classmethod
    def get_properties_model(cls) -> type[BrowserUseProperties]:
        return BrowserUseProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.browser_use",
            name="Browser Use",
            category="ai",
            description="Autonomously browse the web, fill forms, click buttons, and extract data using AI. Powered by browser-use.com.",
            icon="Globe",
            color="#0ea5e9",
            properties=[
                {
                    "name": "credential",
                    "label": "Browser Use API Key",
                    "type": "credential",
                    "credentialType": "browser_use_api_key",
                    "required": True,
                },
                {
                    "name": "task",
                    "label": "Task",
                    "type": "string",
                    "required": True,
                    "placeholder": "Go to example.com and find the price of the first product",
                    "description": "Natural language description of what the browser agent should do.",
                },
                {
                    "name": "start_url",
                    "label": "Start URL",
                    "type": "string",
                    "required": False,
                    "placeholder": "https://example.com",
                    "description": "Optional URL to open before starting the task.",
                },
                {
                    "name": "model",
                    "label": "AI Model",
                    "type": "options",
                    "default": "claude-sonnet-4-5",
                    "options": [
                        {"label": "Claude Sonnet 4.5 (recommended)", "value": "claude-sonnet-4-5"},
                        {"label": "Claude Opus 4.5", "value": "claude-opus-4-5"},
                        {"label": "Claude Haiku 4.5 (fast)", "value": "claude-haiku-4-5"},
                        {"label": "GPT-4o", "value": "gpt-4o"},
                        {"label": "GPT-4o Mini (fast)", "value": "gpt-4o-mini"},
                        {"label": "Gemini 2.0 Flash", "value": "gemini-2.0-flash"},
                        {"label": "Gemini 1.5 Pro", "value": "gemini-1.5-pro"},
                    ],
                },
                {
                    "name": "max_steps",
                    "label": "Max Steps",
                    "type": "number",
                    "default": 50,
                    "description": "Maximum number of browser actions the agent can take.",
                },
                {
                    "name": "allowed_domains",
                    "label": "Allowed Domains",
                    "type": "string",
                    "required": False,
                    "placeholder": "example.com, another.com",
                    "mode": "advanced",
                    "description": "Comma-separated list of domains the agent is allowed to visit.",
                },
                {
                    "name": "secrets",
                    "label": "Secrets / Variables",
                    "type": "json",
                    "required": False,
                    "placeholder": '{"username": "user@example.com", "password": "secret"}',
                    "mode": "advanced",
                    "description": "Key-value pairs injected into the agent context. Use for credentials without exposing them in the task text.",
                },
                {
                    "name": "structured_output",
                    "label": "Structured Output Schema (JSON)",
                    "type": "string",
                    "required": False,
                    "placeholder": '{"type":"object","properties":{"price":{"type":"string"}}}',
                    "mode": "advanced",
                    "description": "JSON Schema to constrain the agent output format.",
                },
                {
                    "name": "system_prompt_extension",
                    "label": "System Prompt Extension",
                    "type": "string",
                    "required": False,
                    "mode": "advanced",
                    "description": "Additional instructions appended to the agent system prompt.",
                },
                {
                    "name": "vision",
                    "label": "Enable Vision",
                    "type": "boolean",
                    "default": True,
                    "mode": "advanced",
                    "description": "Allow the agent to see and interact with visual page elements.",
                },
                {
                    "name": "flash_mode",
                    "label": "Flash Mode (faster, less careful)",
                    "type": "boolean",
                    "default": False,
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "output", "type": "string"},
                {"label": "steps", "type": "array"},
                {"label": "task_id", "type": "string"},
                {"label": "live_url", "type": "string"},
                {"label": "share_url", "type": "string"},
                {"label": "status", "type": "string"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.task.strip():
            return NodeResult(success=False, error="Task is required.")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error="Browser Use API key required.")

        headers = {
            "X-Browser-Use-API-Key": api_key,
            "Content-Type": "application/json",
        }

        # Build request body
        body: dict[str, Any] = {
            "task": self.props.task,
            "model": self.props.model,
            "max_steps": max(1, min(self.props.max_steps, 200)),
            "use_vision": self.props.vision,
        }

        if self.props.start_url and self.props.start_url.strip():
            body["start_url"] = self.props.start_url.strip()

        if self.props.allowed_domains:
            domains = [d.strip() for d in self.props.allowed_domains.split(",") if d.strip()]
            if domains:
                body["allowed_domains"] = domains

        if self.props.secrets and isinstance(self.props.secrets, dict):
            body["secrets"] = self.props.secrets

        if self.props.structured_output and self.props.structured_output.strip():
            import json as _json

            try:
                body["structured_output_json"] = _json.loads(self.props.structured_output)
            except Exception:
                body["structured_output_json"] = self.props.structured_output

        if self.props.system_prompt_extension and self.props.system_prompt_extension.strip():
            body["save_browser_data"] = False  # default
            body["system_prompt_extension"] = self.props.system_prompt_extension.strip()

        if self.props.flash_mode:
            body["flash_mode"] = True

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create task
                resp = await client.post(
                    f"{BROWSER_USE_BASE}/tasks",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                task_data = resp.json()

            task_id = task_data.get("id") or task_data.get("task_id")
            if not task_id:
                return NodeResult(
                    success=False,
                    error=f"Browser Use API did not return a task ID. Response: {task_data}",
                )

            logger.info(f"Browser Use task created: {task_id}")

            # Poll for completion
            elapsed = 0.0
            consecutive_errors = 0
            result_data: dict[str, Any] = {}

            async with httpx.AsyncClient(timeout=30.0) as client:
                while elapsed < MAX_WAIT:
                    await asyncio.sleep(POLL_INTERVAL)
                    elapsed += POLL_INTERVAL

                    try:
                        status_resp = await client.get(
                            f"{BROWSER_USE_BASE}/tasks/{task_id}",
                            headers=headers,
                        )
                        status_resp.raise_for_status()
                        result_data = status_resp.json()
                        consecutive_errors = 0
                    except Exception as poll_err:
                        consecutive_errors += 1
                        logger.warning(f"Browser Use poll error ({consecutive_errors}): {poll_err}")
                        if consecutive_errors >= 3:
                            return NodeResult(
                                success=False,
                                error=f"Polling failed after 3 consecutive errors: {poll_err}",
                            )
                        continue

                    status = result_data.get("status", "")
                    logger.info(
                        f"Browser Use task {task_id} status: {status} ({elapsed:.0f}s elapsed)"
                    )

                    if status in TERMINAL_STATES:
                        break

            status = result_data.get("status", "unknown")
            output = result_data.get("output") or result_data.get("result")
            steps = result_data.get("steps") or []
            live_url = result_data.get("live_url") or result_data.get("liveUrl")
            share_url = result_data.get("share_url") or result_data.get("shareUrl")

            if status == "finished":
                return NodeResult(
                    success=True,
                    output_data={
                        "output": output,
                        "steps": steps,
                        "task_id": task_id,
                        "live_url": live_url,
                        "share_url": share_url,
                        "status": status,
                        "step_count": len(steps),
                    },
                )
            elif status == "failed":
                error_msg = result_data.get("error") or output or "Task failed"
                return NodeResult(success=False, error=f"Browser task failed: {error_msg}")
            else:
                # Timeout or stopped
                return NodeResult(
                    success=False,
                    error=f"Browser task did not complete (status: {status}, elapsed: {elapsed:.0f}s)",
                )

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False,
                error=f"Browser Use API error {e.response.status_code}: {e.response.text[:300]}",
            )
        except Exception as e:
            logger.error(f"BrowserUseNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    def _get_api_key(self, context: NodeContext) -> str | None:
        credentials = context.credentials or []
        cred = None
        if self.props.credential:
            cred = next(
                (
                    c
                    for c in credentials
                    if str(c.get("id")) == str(self.props.credential)
                    and c.get("type") == "browser_use_api_key"
                ),
                None,
            )
        if cred is None:
            cred = next((c for c in credentials if c.get("type") == "browser_use_api_key"), None)
        data = cred.get("data") if cred else None
        if not isinstance(data, dict):
            return None
        key = data.get("api_key")
        return key if isinstance(key, str) and key.strip() else None
