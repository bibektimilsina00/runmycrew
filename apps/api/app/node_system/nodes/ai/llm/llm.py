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


class LLMProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    model: str | None = None
    messages: list[dict[str, Any]] = []
    temperature: float | None = None
    max_tokens: int | None = None
    response_format: str = "text"  # "text" | "json"


class LLMNode(BaseNode[LLMProperties]):
    @classmethod
    def get_properties_model(cls) -> type[LLMProperties]:
        return LLMProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.llm",
            name="LLM",
            category="ai",
            description="Generate text with any LLM. Simple prompt in, text out — no tools or agentic loop.",
            icon="Sparkles",
            color="#6366f1",
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "options",
                    "default": "openai",
                    "required": True,
                    "placeholder": "Type or select an AI provider",
                    "loadOptions": "/ai/providers",
                    "typeOptions": {"searchable": True, "allowCustom": True},
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
                            "openai": "openai_api_key",
                            "anthropic": "anthropic_api_key",
                            "google": "google_api_key",
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
                    "type": "options",
                    "required": True,
                    "placeholder": "Type or select a model ID",
                    "loadOptions": "/ai/models",
                    "loadOptionsDependsOn": ["provider", "credential"],
                    "typeOptions": {"searchable": True, "allowCustom": True},
                },
                {
                    "name": "messages",
                    "label": "Messages",
                    "type": "messages",
                    "required": True,
                    "default": [
                        {"role": "user", "content": "{{trigger.output}}"},
                    ],
                    "description": "Prompt messages with role and content.",
                },
                {
                    "name": "response_format",
                    "label": "Response Format",
                    "type": "options",
                    "default": "text",
                    "options": [
                        {"label": "Text", "value": "text"},
                        {"label": "JSON", "value": "json"},
                    ],
                },
                {
                    "name": "temperature",
                    "label": "Temperature",
                    "type": "number",
                    "default": 0.7,
                    "mode": "advanced",
                },
                {
                    "name": "max_tokens",
                    "label": "Max Tokens",
                    "type": "number",
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "text", "type": "string"},
                {"label": "tokens", "type": "object"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.messages or not any(
            isinstance(m, dict) and str(m.get("content", "")).strip() for m in self.props.messages
        ):
            return NodeResult(success=False, error="At least one non-empty message is required.")

        ai_provider = get_ai_provider(self.props.provider)
        if not ai_provider:
            return NodeResult(success=False, error=f"Unknown provider: {self.props.provider}")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error=f"{ai_provider.name} credential required.")

        model = self.props.model or ai_provider.default_model or ""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if ai_provider.ai_api_type == "openai_compatible":
                    text, tokens = await self._call_openai(
                        client, ai_provider.chat_completions_url or "", api_key, model
                    )
                elif ai_provider.ai_api_type == "anthropic":
                    text, tokens = await self._call_anthropic(
                        client, ai_provider.chat_completions_url or "", api_key, model
                    )
                elif ai_provider.ai_api_type == "google":
                    text, tokens = await self._call_google(
                        client, ai_provider.chat_completions_url or "", api_key, model
                    )
                else:
                    return NodeResult(
                        success=False, error=f"Unsupported provider type: {ai_provider.ai_api_type}"
                    )

            return NodeResult(success=True, output_data={"text": text, "tokens": tokens})

        except httpx.HTTPStatusError as e:
            # Surface the URL + a hint for the common 404 case so the
            # user isn't left with "API error 404:" and no body to
            # diagnose against. Most provider 404s mean the model id
            # is retired or unknown to the account.
            body = (e.response.text or "").strip()[:300]
            hint = ""
            if e.response.status_code == 404:
                hint = (
                    f" — likely the model id ({model!r}) is unknown "
                    "to this provider account or has been retired. "
                    "Check the model dropdown on the LLM node."
                )
            elif e.response.status_code in (401, 403):
                hint = " — credential / API key is invalid or missing permission for this model."
            return NodeResult(
                success=False,
                error=(
                    f"API error {e.response.status_code} on "
                    f"{e.request.url}: {body or '(no response body)'}"
                    f"{hint}"
                ),
            )
        except Exception as e:
            logger.error(f"LLMNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    def _messages(self) -> list[dict[str, Any]]:
        """Normalise the configured messages list into provider-neutral shape."""
        msgs: list[dict[str, Any]] = []
        for m in self.props.messages or []:
            if not isinstance(m, dict):
                continue
            role = m.get("role") or "user"
            if role not in {"system", "user", "assistant"}:
                role = "user"
            content = str(m.get("content", ""))
            msgs.append({"role": role, "content": content})
        return msgs

    async def _call_openai(
        self, client: httpx.AsyncClient, url: str, api_key: str, model: str
    ) -> tuple[str, dict]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": self._messages(),
        }
        if self.props.temperature is not None:
            payload["temperature"] = self.props.temperature
        if self.props.max_tokens is not None:
            payload["max_tokens"] = self.props.max_tokens
        if self.props.response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        usage = data.get("usage") or {}
        return text, {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }

    async def _call_anthropic(
        self, client: httpx.AsyncClient, url: str, api_key: str, model: str
    ) -> tuple[str, dict]:
        msgs = self._messages()
        system = next((m["content"] for m in msgs if m["role"] == "system"), None)
        user_msgs = [m for m in msgs if m["role"] != "system"]

        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": self.props.max_tokens or 4096,
            "messages": user_msgs,
        }
        if system:
            payload["system"] = system
        if self.props.temperature is not None:
            payload["temperature"] = self.props.temperature
        if self.props.response_format == "json":
            payload["system"] = (system or "") + "\nRespond with valid JSON only."

        resp = await client.post(
            url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content") or []
        text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
        usage = data.get("usage") or {}
        return text, {
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens"),
            "total_tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
        }

    async def _call_google(
        self, client: httpx.AsyncClient, url_template: str, api_key: str, model: str
    ) -> tuple[str, dict]:
        msgs = self._messages()
        system = next((m["content"] for m in msgs if m["role"] == "system"), None)
        contents = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
            for m in msgs
            if m["role"] != "system"
        ]

        generation_config: dict[str, Any] = {}
        if self.props.temperature is not None:
            generation_config["temperature"] = self.props.temperature
        if self.props.max_tokens is not None:
            generation_config["maxOutputTokens"] = self.props.max_tokens
        if self.props.response_format == "json":
            generation_config["responseMimeType"] = "application/json"

        payload: dict[str, Any] = {"contents": contents}
        if generation_config:
            payload["generationConfig"] = generation_config
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        # Normalise model path (models/gemini-... or just gemini-...)
        model_path = model if model.startswith("models/") else f"models/{model}"
        url = url_template.format(model=model_path)

        resp = await client.post(
            url, params={"key": api_key}, headers={"Content-Type": "application/json"}, json=payload
        )
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        text = ""
        if candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata") or {}
        return text, {
            "prompt_tokens": usage.get("promptTokenCount"),
            "completion_tokens": usage.get("candidatesTokenCount"),
            "total_tokens": usage.get("totalTokenCount"),
        }

    def _get_api_key(self, context: NodeContext) -> str | None:
        ai_provider = get_ai_provider(self.props.provider)
        if not ai_provider:
            return None
        credentials = context.credentials or []
        cred = None
        if self.props.credential:
            cred = next(
                (
                    c
                    for c in credentials
                    if str(c.get("id")) == str(self.props.credential)
                    and c.get("type") == ai_provider.id
                ),
                None,
            )
        if cred is None:
            cred = next((c for c in credentials if c.get("type") == ai_provider.id), None)
        data = cred.get("data") if cred else None
        if not isinstance(data, dict):
            return None
        key = data.get("api_key")
        return key if isinstance(key, str) and key.strip() else None
