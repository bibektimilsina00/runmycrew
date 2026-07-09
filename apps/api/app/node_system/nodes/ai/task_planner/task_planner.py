from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, Field

from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.api_keys import get_ai_provider, get_ai_providers
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.task_planner import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)


class TaskPlannerProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    openaiCredential: str | None = None
    anthropicCredential: str | None = None
    googleCredential: str | None = None
    groqCredential: str | None = None
    model: str | None = None
    goal: str = ""
    available_roles: list[str] | str = Field(default_factory=list)
    max_tasks: int = 8
    temperature: float = 0.2


class TaskPlannerNode(BaseNode[TaskPlannerProperties]):
    @classmethod
    def get_properties_model(cls) -> type[TaskPlannerProperties]:
        return TaskPlannerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="ai.task_planner",
            name=NAME,
            category="ai",
            description=(
                "Decompose a goal into a task DAG. Each task gets an assignee role, "
                "expected output, and dependency list — feeds directly into a Parallel node."
            ),
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "options",
                    "default": "openai",
                    "required": True,
                    "loadOptions": "/ai/providers",
                    "typeOptions": {"searchable": True, "allowCustom": True},
                },
                *cls._provider_credential_properties(),
                {
                    "name": "credential",
                    "label": "Provider Credential",
                    "type": "credential",
                    "required": True,
                    "dependsOn": ["provider"],
                    "credentialTypeByField": {
                        "field": "provider",
                        "values": cls._credential_type_by_provider(),
                    },
                },
                {
                    "name": "model",
                    "label": "Model",
                    "type": "options",
                    "required": True,
                    "loadOptions": "/ai/models",
                    "loadOptionsDependsOn": [
                        "provider",
                        "credential",
                        "openaiCredential",
                        "anthropicCredential",
                        "googleCredential",
                        "groqCredential",
                    ],
                    "typeOptions": {"searchable": True, "allowCustom": True},
                },
                {
                    "name": "goal",
                    "label": "Goal",
                    "type": "string",
                    "required": True,
                    "placeholder": "Research 3 competitors and write a comparison.",
                    "description": "High-level goal to decompose into tasks.",
                },
                {
                    "name": "available_roles",
                    "label": "Available Roles",
                    "type": "list",
                    "default": ["researcher", "writer", "reviewer"],
                    "description": "Persona role tags the planner may assign tasks to.",
                },
                {
                    "name": "max_tasks",
                    "label": "Max Tasks",
                    "type": "number",
                    "default": 8,
                    "mode": "advanced",
                },
                {
                    "name": "temperature",
                    "label": "Temperature",
                    "type": "number",
                    "default": 0.2,
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "tasks", "type": "array"},
                {"label": "goal", "type": "string"},
                {"label": "count", "type": "number"},
            ],
            allow_error=True,
        )

    @classmethod
    def _provider_credential_properties(cls) -> list[dict[str, Any]]:
        creds = [
            {
                "name": "openaiCredential",
                "label": "OpenAI API Key",
                "type": "credential",
                "credentialType": "openai_api_key",
                "required": {"field": "provider", "value": "openai"},
                "condition": {"field": "provider", "value": "openai"},
            },
            {
                "name": "anthropicCredential",
                "label": "Anthropic API Key",
                "type": "credential",
                "credentialType": "anthropic_api_key",
                "required": {"field": "provider", "value": "anthropic"},
                "condition": {"field": "provider", "value": "anthropic"},
            },
            {
                "name": "googleCredential",
                "label": "Google API Key",
                "type": "credential",
                "credentialType": "google_api_key",
                "required": {"field": "provider", "value": "google"},
                "condition": {"field": "provider", "value": "google"},
            },
            {
                "name": "groqCredential",
                "label": "Groq API Key",
                "type": "credential",
                "credentialType": "groq_api_key",
                "required": {"field": "provider", "value": "groq"},
                "condition": {"field": "provider", "value": "groq"},
            },
        ]
        catalog = {p.ai_provider_id: p for p in get_ai_providers()}
        for c in creds:
            pid = c["condition"]["value"]
            if catalog.get(pid):
                c["label"] = f"{catalog[pid].name} API Key"
                c["credentialType"] = catalog[pid].id
            c["visibility"] = "hidden"
        return creds

    @classmethod
    def _credential_type_by_provider(cls) -> dict[str, str]:
        return {p.ai_provider_id: p.id for p in get_ai_providers() if p.ai_provider_id}

    def _get_api_key(self, context: NodeContext) -> str | None:
        provider_field = f"{self.props.provider}Credential"
        cred_id = getattr(self.props, provider_field, None) or self.props.credential
        if not cred_id:
            return None
        for c in context.credentials or []:
            if str(c.get("id")) == str(cred_id):
                data = c.get("data") or {}
                return data.get("api_key") or data.get("key") or data.get("token")
        return None

    def _roles(self) -> list[str]:
        raw = self.props.available_roles
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                return [str(r) for r in parsed] if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return [r.strip() for r in raw.split(",") if r.strip()]
        return [str(r) for r in raw or []]

    def _build_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "expected_output": {"type": "string"},
                            "assignee_role": {"type": "string"},
                            "depends_on": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "id",
                            "name",
                            "description",
                            "expected_output",
                            "assignee_role",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["tasks"],
            "additionalProperties": False,
        }

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        goal = (self.props.goal or "").strip()
        if not goal:
            return NodeResult(success=False, error="Goal is required.")

        ai_provider = get_ai_provider(self.props.provider)
        if not ai_provider:
            return NodeResult(success=False, error=f"Unknown provider: {self.props.provider}")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error=f"{ai_provider.name} credential required.")

        roles = self._roles()
        role_str = ", ".join(roles) if roles else "any"
        system_prompt = (
            "You are a project planner. Decompose the user's goal into concrete tasks. "
            f"Available roles: {role_str}. "
            f"Return AT MOST {self.props.max_tasks} tasks. Each task must have a stable id "
            "(e.g. t1, t2), a short name, a description, an expected_output, an assignee_role "
            "from the available roles, and depends_on (list of task ids). "
            "Order tasks so a dependency graph can be resolved."
        )

        model = self.props.model or (ai_provider.default_model or "")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": goal},
        ]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if ai_provider.ai_api_type == "openai_compatible":
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": self.props.temperature,
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "task_plan",
                                "schema": self._build_schema(),
                                "strict": True,
                            },
                        },
                    }
                    resp = await client.post(
                        ai_provider.chat_completions_url or "",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                elif ai_provider.ai_api_type == "anthropic":
                    payload = {
                        "model": model,
                        "max_tokens": 2048,
                        "temperature": self.props.temperature,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": goal}],
                    }
                    resp = await client.post(
                        ai_provider.chat_completions_url or "",
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    parts = data.get("content") or []
                    content = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
                else:
                    return NodeResult(
                        success=False,
                        error=f"Unsupported provider api type: {ai_provider.ai_api_type}",
                    )
        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"Planner LLM call failed: {e.response.text[:200]}"
            )

        try:
            plan = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            # Anthropic sometimes fences JSON; take longest {...} slice.
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end <= start:
                return NodeResult(success=False, error="Planner did not return JSON.")
            try:
                plan = json.loads(content[start : end + 1])
            except json.JSONDecodeError as e:
                return NodeResult(success=False, error=f"Planner JSON malformed: {e}")

        tasks = plan.get("tasks") or []
        if not isinstance(tasks, list):
            return NodeResult(success=False, error="Planner returned no tasks list.")
        # Cap and normalise
        tasks = tasks[: max(self.props.max_tasks, 1)]
        for i, t in enumerate(tasks):
            if not isinstance(t, dict):
                continue
            t.setdefault("id", f"t{i + 1}")
            t.setdefault("depends_on", [])

        return NodeResult(
            success=True,
            output_data={"tasks": tasks, "goal": goal, "count": len(tasks)},
        )
