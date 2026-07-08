from __future__ import annotations

import base64
from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.stt import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)


class STTProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    model: str = "whisper-1"
    audio_url: str | None = None
    language: str | None = None
    prompt: str | None = None


class STTNode(BaseNode[STTProperties]):
    @classmethod
    def get_properties_model(cls) -> type[STTProperties]:
        return STTProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.stt",
            name=NAME,
            category="ai",
            description="Transcribe audio to text using OpenAI Whisper or Groq. Accepts audio URLs or base64 data URIs.",
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "options",
                    "default": "openai",
                    "options": [
                        {"label": "OpenAI Whisper", "value": "openai"},
                        {"label": "Groq Whisper (faster)", "value": "groq"},
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
                            "groq": "groq_api_key",
                        },
                    },
                },
                {
                    "name": "model",
                    "label": "Model",
                    "type": "options",
                    "default": "whisper-1",
                    "options": [
                        {"label": "whisper-1 (OpenAI)", "value": "whisper-1"},
                        {"label": "whisper-large-v3 (Groq)", "value": "whisper-large-v3"},
                        {
                            "label": "whisper-large-v3-turbo (Groq, fast)",
                            "value": "whisper-large-v3-turbo",
                        },
                        {
                            "label": "distil-whisper-large-v3-en (Groq, English)",
                            "value": "distil-whisper-large-v3-en",
                        },
                    ],
                },
                {
                    "name": "audio_url",
                    "label": "Audio URL or Data URI",
                    "type": "string",
                    "required": True,
                    "placeholder": "https://example.com/audio.mp3 or data:audio/mp3;base64,...",
                    "description": "Public audio URL or base64 data URI. Supported: mp3, mp4, mpeg, mpga, m4a, wav, webm",
                },
                {
                    "name": "language",
                    "label": "Language",
                    "type": "string",
                    "required": False,
                    "placeholder": "en",
                    "mode": "advanced",
                    "description": "ISO-639-1 language code (e.g. en, es, fr). Leave blank for auto-detect.",
                },
                {
                    "name": "prompt",
                    "label": "Prompt",
                    "type": "string",
                    "required": False,
                    "mode": "advanced",
                    "description": "Optional hint text to guide transcription style or vocabulary.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "transcript", "type": "string"},
                {"label": "language", "type": "string"},
                {"label": "duration", "type": "number"},
                {"label": "segments", "type": "array"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.audio_url:
            return NodeResult(success=False, error="Audio URL is required.")

        api_key, endpoint = self._provider_config(context)
        if not api_key:
            return NodeResult(success=False, error=f"{self.props.provider} credential required.")

        try:
            audio_bytes, filename = await self._fetch_audio(self.props.audio_url)
        except Exception as e:
            return NodeResult(success=False, error=f"Failed to fetch audio: {e}")

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                files = {"file": (filename, audio_bytes, "audio/mpeg")}
                data: dict[str, Any] = {
                    "model": self.props.model,
                    "response_format": "verbose_json",
                }
                if self.props.language:
                    data["language"] = self.props.language
                if self.props.prompt:
                    data["prompt"] = self.props.prompt

                resp = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files,
                    data=data,
                )
                resp.raise_for_status()
                result = resp.json()

            return NodeResult(
                success=True,
                output_data={
                    "transcript": result.get("text", ""),
                    "language": result.get("language"),
                    "duration": result.get("duration"),
                    "segments": result.get("segments") or [],
                },
            )

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"API error {e.response.status_code}: {e.response.text[:300]}"
            )
        except Exception as e:
            logger.error(f"STTNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    async def _fetch_audio(self, url: str) -> tuple[bytes, str]:
        if url.startswith("data:"):
            # data:audio/mp3;base64,<data>
            header, data = url.split(",", 1)
            ext = header.split(";")[0].split("/")[-1]
            return base64.b64decode(data), f"audio.{ext}"
        # Download from URL
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            ext = url.split("?")[0].rsplit(".", 1)[-1] if "." in url else "mp3"
            return resp.content, f"audio.{ext}"

    def _provider_config(self, context: NodeContext) -> tuple[str | None, str]:
        type_map = {"openai": "openai_api_key", "groq": "groq_api_key"}
        endpoint_map = {
            "openai": "https://api.openai.com/v1/audio/transcriptions",
            "groq": "https://api.groq.com/openai/v1/audio/transcriptions",
        }
        cred_type = type_map.get(self.props.provider, "openai_api_key")
        endpoint = endpoint_map.get(
            self.props.provider, "https://api.openai.com/v1/audio/transcriptions"
        )
        credentials = context.credentials or []
        cred = None
        if self.props.credential:
            cred = next(
                (
                    c
                    for c in credentials
                    if str(c.get("id")) == str(self.props.credential) and c.get("type") == cred_type
                ),
                None,
            )
        if cred is None:
            cred = next((c for c in credentials if c.get("type") == cred_type), None)
        data = cred.get("data") if cred else None
        if not isinstance(data, dict):
            return None, endpoint
        key = data.get("api_key")
        return (key if isinstance(key, str) and key.strip() else None), endpoint
