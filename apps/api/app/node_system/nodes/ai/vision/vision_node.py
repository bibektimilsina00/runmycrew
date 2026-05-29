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

# Vision-capable models per provider
VISION_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-vision-preview"],
    "anthropic": [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-opus-4-7",
    ],
    "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"],
}


class VisionProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    model: str | None = None
    image_url: str | None = None
    prompt: str = "Describe this image in detail."
    max_tokens: int | None = None


class VisionNode(BaseNode[VisionProperties]):
    @classmethod
    def get_properties_model(cls) -> type[VisionProperties]:
        return VisionProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.vision",
            name="Vision",
            category="ai",
            description="Analyze images with AI. Pass an image URL and a prompt, get back a text description or answer.",
            icon="Eye",
            color="#ec4899",
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "options",
                    "default": "openai",
                    "options": [
                        {"label": "OpenAI (GPT-4o)", "value": "openai"},
                        {"label": "Anthropic (Claude)", "value": "anthropic"},
                        {"label": "Google (Gemini)", "value": "google"},
                    ],
                },
                {
                    "name": "credential",
                    "label": "Credential",
                    "type": "credential",
                    "required": True,
                    "credentialTypeByField": {
                        "field": "provider",
                        "values": {
                            "openai": "openai_api_key",
                            "anthropic": "anthropic_api_key",
                            "google": "google_api_key",
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
                    "name": "image_url",
                    "label": "Image URL",
                    "type": "string",
                    "required": True,
                    "placeholder": "https://example.com/image.jpg or data:image/jpeg;base64,...",
                    "description": "Public image URL or base64 data URI",
                },
                {
                    "name": "prompt",
                    "label": "Prompt",
                    "type": "string",
                    "required": True,
                    "default": "Describe this image in detail.",
                    "placeholder": "What is shown in this image?",
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
                {"label": "model", "type": "string"},
                {"label": "tokens", "type": "object"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.image_url:
            return NodeResult(success=False, error="Image URL is required.")
        if not self.props.prompt.strip():
            return NodeResult(success=False, error="Prompt is required.")

        ai_provider = get_ai_provider(self.props.provider)
        if not ai_provider:
            return NodeResult(success=False, error=f"Unknown provider: {self.props.provider}")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error=f"{ai_provider.name} credential required.")

        model = self.props.model or _default_model(self.props.provider)

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
                        success=False,
                        error=f"Provider {self.props.provider} does not support vision.",
                    )

            return NodeResult(
                success=True, output_data={"text": text, "model": model, "tokens": tokens}
            )

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"API error {e.response.status_code}: {e.response.text[:300]}"
            )
        except Exception as e:
            logger.error(f"VisionNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    def _image_content(self, provider: str) -> Any:
        """Return provider-specific image content block."""
        url = self.props.image_url or ""
        is_base64 = url.startswith("data:")

        if provider == "openai":
            if is_base64:
                return {"type": "image_url", "image_url": {"url": url}}
            return {"type": "image_url", "image_url": {"url": url, "detail": "auto"}}

        if provider == "anthropic":
            if is_base64:
                # data:image/jpeg;base64,<data>
                header, data = url.split(",", 1)
                media_type = header.split(";")[0].replace("data:", "")
                return {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": data},
                }
            return {"type": "image", "source": {"type": "url", "url": url}}

        if provider == "google":
            if is_base64:
                header, data = url.split(",", 1)
                mime_type = header.split(";")[0].replace("data:", "")
                return {"inline_data": {"mime_type": mime_type, "data": data}}
            return {"file_data": {"mime_type": "image/jpeg", "file_uri": url}}

        return url

    async def _call_openai(
        self, client: httpx.AsyncClient, url: str, api_key: str, model: str
    ) -> tuple[str, dict]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        self._image_content("openai"),
                        {"type": "text", "text": self.props.prompt},
                    ],
                }
            ],
        }
        if self.props.max_tokens:
            payload["max_tokens"] = self.props.max_tokens

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
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": self.props.max_tokens or 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        self._image_content("anthropic"),
                        {"type": "text", "text": self.props.prompt},
                    ],
                }
            ],
        }
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
        image_part = self._image_content("google")
        parts: list[Any] = [image_part, {"text": self.props.prompt}]

        generation_config: dict[str, Any] = {}
        if self.props.max_tokens:
            generation_config["maxOutputTokens"] = self.props.max_tokens

        payload: dict[str, Any] = {"contents": [{"role": "user", "parts": parts}]}
        if generation_config:
            payload["generationConfig"] = generation_config

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
            parts_out = (candidates[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts_out)
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


def _default_model(provider: str) -> str:
    return {"openai": "gpt-4o", "anthropic": "claude-sonnet-4-5", "google": "gemini-1.5-flash"}.get(
        provider, "gpt-4o"
    )
