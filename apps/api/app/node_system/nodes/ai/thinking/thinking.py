from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.api_keys import get_ai_provider
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

_EFFORT_BUDGET = {"low": 1024, "medium": 8192, "high": 32768}


class ThinkingProperties(BaseModel):
    provider: str = "anthropic"
    credential: str | None = None
    model: str | None = None
    prompt: str = ""
    budgetTokens: int = 8192
    temperature: float = 1.0  # Anthropic extended thinking requires temp=1


class ThinkingNode(BaseNode[ThinkingProperties]):
    @classmethod
    def get_properties_model(cls) -> type[ThinkingProperties]:
        return ThinkingProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.thinking",
            name="Thinking",
            category="ai",
            description="Run a chain-of-thought reasoning step. Shows the model's thinking process.",
            icon="Brain",
            color="#8b5cf6",
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "string",
                    "default": "anthropic",
                    "loadOptions": "/ai/providers",
                },
                {
                    "name": "credential",
                    "label": "Credential",
                    "type": "credential",
                    "required": True,
                    "dependsOn": ["provider"],
                    "credentialTypeByField": {
                        "field": "provider",
                        "values": {
                            "anthropic": "anthropic_api_key",
                            "openai": "openai_api_key",
                            "groq": "groq_api_key",
                            "openrouter": "openrouter_api_key",
                            "deepseek": "deepseek_api_key",
                            "mistral": "mistral_api_key",
                            "xai": "xai_api_key",
                            "together": "together_api_key",
                            "fireworks": "fireworks_api_key",
                        },
                    },
                },
                {
                    "name": "model",
                    "label": "Model",
                    "type": "string",
                    "required": True,
                    "loadOptions": "/ai/models",
                    "loadOptionsDependsOn": ["provider", "credential"],
                },
                {
                    "name": "prompt",
                    "label": "Prompt",
                    "type": "string",
                    "required": True,
                    "placeholder": "Think through this step by step: {{$trigger.output}}",
                },
                {
                    "name": "budgetTokens",
                    "label": "Thinking Budget (tokens)",
                    "type": "number",
                    "default": 8192,
                    "mode": "advanced",
                    "description": "Max tokens for the thinking process (1024–32768).",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "thinking", "type": "string"},
                {"label": "response", "type": "string"},
                {"label": "tokens", "type": "object"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.prompt.strip():
            return NodeResult(success=False, error="Prompt is required.")

        ai_provider = get_ai_provider(self.props.provider)
        if not ai_provider:
            return NodeResult(success=False, error=f"Unknown provider: {self.props.provider}")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error=f"{ai_provider.name} credential required.")

        model = self.props.model or (ai_provider.default_model or "")
        budget = max(1024, min(self.props.budgetTokens, 32768))

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if ai_provider.ai_api_type == "anthropic":
                    thinking_content, response_text, tokens = await self._call_anthropic(
                        client, ai_provider.chat_completions_url or "", api_key, model, budget
                    )
                elif ai_provider.ai_api_type == "openai_compatible":
                    # For OpenAI o1/o3 reasoning models — reasoning_effort maps to budget
                    thinking_content, response_text, tokens = await self._call_openai_reasoning(
                        client, ai_provider.chat_completions_url or "", api_key, model, budget
                    )
                else:
                    return NodeResult(
                        success=False,
                        error="Thinking node supports Anthropic and OpenAI reasoning models.",
                    )

            return NodeResult(
                success=True,
                output_data={
                    "thinking": thinking_content,
                    "response": response_text,
                    "tokens": tokens,
                },
            )
        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"API error {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))

    async def _call_anthropic(
        self, client: httpx.AsyncClient, url: str, api_key: str, model: str, budget: int
    ) -> tuple[str, str, dict[str, Any]]:
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": budget + 4096,
            "thinking": {"type": "enabled", "budget_tokens": budget},
            "temperature": 1,  # required for extended thinking
            "messages": [{"role": "user", "content": self.props.prompt}],
        }
        response = await client.post(
            url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        thinking_parts: list[str] = []
        text_parts: list[str] = []
        for block in data.get("content") or []:
            if block.get("type") == "thinking":
                thinking_parts.append(block.get("thinking", ""))
            elif block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        usage = data.get("usage") or {}
        tokens = {
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens"),
            "total_tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
        }
        return "\n".join(thinking_parts), "\n".join(text_parts), tokens

    async def _call_openai_reasoning(
        self, client: httpx.AsyncClient, url: str, api_key: str, model: str, budget: int
    ) -> tuple[str, str, dict[str, Any]]:
        effort = "low" if budget <= 2048 else ("high" if budget >= 16384 else "medium")
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": self.props.prompt}],
            "reasoning_effort": effort,
        }
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        usage = data.get("usage") or {}
        tokens = {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get(
                "reasoning_tokens"
            ),
        }
        return "", message.get("content") or "", tokens

    def _get_api_key(self, context: NodeContext) -> str | None:
        ai_provider = get_ai_provider(self.props.provider)
        if not ai_provider:
            return None
        credentials = context.credentials or []
        cred = next(
            (
                c
                for c in credentials
                if c.get("type") == ai_provider.id
                and (not self.props.credential or str(c.get("id")) == str(self.props.credential))
            ),
            None,
        )
        if not cred:
            cred = next((c for c in credentials if c.get("type") == ai_provider.id), None)
        data = cred.get("data") if cred else None
        if not isinstance(data, dict):
            return None
        key = data.get("api_key")
        return key if isinstance(key, str) and key.strip() else None
