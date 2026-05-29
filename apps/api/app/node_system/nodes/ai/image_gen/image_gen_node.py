from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class ImageGenProperties(BaseModel):
    credential: str | None = None
    model: str = "dall-e-3"
    prompt: str = ""
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "vivid"
    n: int = 1
    response_format: str = "url"


class ImageGenNode(BaseNode[ImageGenProperties]):
    @classmethod
    def get_properties_model(cls) -> type[ImageGenProperties]:
        return ImageGenProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.image_gen",
            name="Image Generator",
            category="ai",
            description="Generate images from text prompts using DALL-E 3 or DALL-E 2.",
            icon="ImagePlus",
            color="#a855f7",
            properties=[
                {
                    "name": "credential",
                    "label": "OpenAI Credential",
                    "type": "credential",
                    "credentialType": "openai_api_key",
                    "required": True,
                },
                {
                    "name": "model",
                    "label": "Model",
                    "type": "options",
                    "default": "dall-e-3",
                    "options": [
                        {"label": "DALL-E 3 (best quality)", "value": "dall-e-3"},
                        {"label": "DALL-E 2", "value": "dall-e-2"},
                    ],
                },
                {
                    "name": "prompt",
                    "label": "Prompt",
                    "type": "string",
                    "required": True,
                    "placeholder": "A photorealistic image of {{trigger.subject}}",
                },
                {
                    "name": "size",
                    "label": "Size",
                    "type": "options",
                    "default": "1024x1024",
                    "options": [
                        {"label": "1024×1024 (square)", "value": "1024x1024"},
                        {"label": "1792×1024 (landscape, DALL-E 3)", "value": "1792x1024"},
                        {"label": "1024×1792 (portrait, DALL-E 3)", "value": "1024x1792"},
                        {"label": "512×512 (DALL-E 2)", "value": "512x512"},
                        {"label": "256×256 (DALL-E 2)", "value": "256x256"},
                    ],
                },
                {
                    "name": "quality",
                    "label": "Quality",
                    "type": "options",
                    "default": "standard",
                    "options": [
                        {"label": "Standard", "value": "standard"},
                        {"label": "HD (DALL-E 3 only)", "value": "hd"},
                    ],
                    "condition": {"field": "model", "value": "dall-e-3"},
                },
                {
                    "name": "style",
                    "label": "Style",
                    "type": "options",
                    "default": "vivid",
                    "options": [
                        {"label": "Vivid (hyper-real, dramatic)", "value": "vivid"},
                        {"label": "Natural (realistic, less dramatic)", "value": "natural"},
                    ],
                    "condition": {"field": "model", "value": "dall-e-3"},
                    "mode": "advanced",
                },
                {
                    "name": "n",
                    "label": "Number of Images",
                    "type": "number",
                    "default": 1,
                    "mode": "advanced",
                    "description": "1–10 for DALL-E 2. DALL-E 3 always returns 1.",
                },
                {
                    "name": "response_format",
                    "label": "Response Format",
                    "type": "options",
                    "default": "url",
                    "options": [
                        {"label": "URL (temporary link)", "value": "url"},
                        {"label": "Base64 JSON", "value": "b64_json"},
                    ],
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "url", "type": "string"},
                {"label": "urls", "type": "array"},
                {"label": "revised_prompt", "type": "string"},
                {"label": "model", "type": "string"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.prompt.strip():
            return NodeResult(success=False, error="Prompt is required.")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error="OpenAI credential required.")

        payload: dict[str, Any] = {
            "model": self.props.model,
            "prompt": self.props.prompt,
            "size": self.props.size,
            "response_format": self.props.response_format,
            "n": max(1, min(self.props.n, 10 if self.props.model == "dall-e-2" else 1)),
        }

        if self.props.model == "dall-e-3":
            payload["quality"] = self.props.quality
            payload["style"] = self.props.style

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            images = data.get("data") or []
            if self.props.response_format == "url":
                urls = [img.get("url", "") for img in images]
                first_url = urls[0] if urls else ""
                revised_prompt = images[0].get("revised_prompt") if images else None
                return NodeResult(
                    success=True,
                    output_data={
                        "url": first_url,
                        "urls": urls,
                        "revised_prompt": revised_prompt,
                        "model": self.props.model,
                    },
                )
            else:
                b64_images = [img.get("b64_json", "") for img in images]
                first = b64_images[0] if b64_images else ""
                return NodeResult(
                    success=True,
                    output_data={
                        "url": f"data:image/png;base64,{first}" if first else "",
                        "urls": [f"data:image/png;base64,{b}" for b in b64_images],
                        "revised_prompt": images[0].get("revised_prompt") if images else None,
                        "model": self.props.model,
                    },
                )

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"API error {e.response.status_code}: {e.response.text[:300]}"
            )
        except Exception as e:
            logger.error(f"ImageGenNode failed: {e}", exc_info=True)
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
                    and c.get("type") == "openai_api_key"
                ),
                None,
            )
        if cred is None:
            cred = next((c for c in credentials if c.get("type") == "openai_api_key"), None)
        data = cred.get("data") if cred else None
        if not isinstance(data, dict):
            return None
        key = data.get("api_key")
        return key if isinstance(key, str) and key.strip() else None
