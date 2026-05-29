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

logger = get_logger(__name__)


class TTSProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    elevenlabs_credential: str | None = None
    model: str = "tts-1"
    voice: str = "alloy"
    elevenlabs_voice_id: str = ""
    elevenlabs_model: str = "eleven_multilingual_v2"
    text: str = ""
    speed: float = 1.0
    response_format: str = "mp3"


class TTSNode(BaseNode[TTSProperties]):
    @classmethod
    def get_properties_model(cls) -> type[TTSProperties]:
        return TTSProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.tts",
            name="Text to Speech",
            category="ai",
            description="Convert text to natural-sounding speech. Returns base64-encoded audio.",
            icon="Volume2",
            color="#10b981",
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "options",
                    "default": "openai",
                    "options": [
                        {"label": "OpenAI", "value": "openai"},
                        {"label": "ElevenLabs", "value": "elevenlabs"},
                    ],
                },
                # OpenAI
                {
                    "name": "credential",
                    "label": "OpenAI Credential",
                    "type": "credential",
                    "credentialType": "openai_api_key",
                    "required": True,
                    "condition": {"field": "provider", "value": "openai"},
                },
                {
                    "name": "model",
                    "label": "Model",
                    "type": "options",
                    "default": "tts-1",
                    "options": [
                        {"label": "TTS-1 (fast)", "value": "tts-1"},
                        {"label": "TTS-1-HD (higher quality)", "value": "tts-1-hd"},
                    ],
                    "condition": {"field": "provider", "value": "openai"},
                },
                {
                    "name": "voice",
                    "label": "Voice",
                    "type": "options",
                    "default": "alloy",
                    "options": [
                        {"label": "Alloy", "value": "alloy"},
                        {"label": "Echo", "value": "echo"},
                        {"label": "Fable", "value": "fable"},
                        {"label": "Onyx", "value": "onyx"},
                        {"label": "Nova", "value": "nova"},
                        {"label": "Shimmer", "value": "shimmer"},
                    ],
                    "condition": {"field": "provider", "value": "openai"},
                },
                {
                    "name": "response_format",
                    "label": "Format",
                    "type": "options",
                    "default": "mp3",
                    "options": [
                        {"label": "MP3", "value": "mp3"},
                        {"label": "Opus", "value": "opus"},
                        {"label": "AAC", "value": "aac"},
                        {"label": "FLAC", "value": "flac"},
                        {"label": "WAV", "value": "wav"},
                    ],
                    "condition": {"field": "provider", "value": "openai"},
                    "mode": "advanced",
                },
                {
                    "name": "speed",
                    "label": "Speed",
                    "type": "number",
                    "default": 1.0,
                    "mode": "advanced",
                    "condition": {"field": "provider", "value": "openai"},
                    "description": "0.25 to 4.0",
                },
                # ElevenLabs
                {
                    "name": "elevenlabs_credential",
                    "label": "ElevenLabs Credential",
                    "type": "credential",
                    "credentialType": "elevenlabs_api_key",
                    "required": True,
                    "condition": {"field": "provider", "value": "elevenlabs"},
                },
                {
                    "name": "elevenlabs_voice_id",
                    "label": "Voice ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "21m00Tcm4TlvDq8ikWAM",
                    "condition": {"field": "provider", "value": "elevenlabs"},
                    "description": "Voice ID from your ElevenLabs account",
                },
                {
                    "name": "elevenlabs_model",
                    "label": "Model",
                    "type": "options",
                    "default": "eleven_multilingual_v2",
                    "options": [
                        {"label": "Multilingual v2", "value": "eleven_multilingual_v2"},
                        {"label": "Monolingual v1", "value": "eleven_monolingual_v1"},
                        {"label": "Turbo v2.5 (fast)", "value": "eleven_turbo_v2_5"},
                    ],
                    "condition": {"field": "provider", "value": "elevenlabs"},
                },
                # Shared
                {
                    "name": "text",
                    "label": "Text",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{llm.text}}",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "audio_base64", "type": "string"},
                {"label": "audio_data_uri", "type": "string"},
                {"label": "format", "type": "string"},
                {"label": "provider", "type": "string"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.text.strip():
            return NodeResult(success=False, error="Text is required.")

        try:
            if self.props.provider == "openai":
                return await self._openai_tts(context)
            elif self.props.provider == "elevenlabs":
                return await self._elevenlabs_tts(context)
            else:
                return NodeResult(success=False, error=f"Unknown provider: {self.props.provider}")
        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"API error {e.response.status_code}: {e.response.text[:300]}"
            )
        except Exception as e:
            logger.error(f"TTSNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    async def _openai_tts(self, context: NodeContext) -> NodeResult:
        api_key = self._get_cred_key(context, "openai_api_key", self.props.credential)
        if not api_key:
            return NodeResult(success=False, error="OpenAI credential required.")

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.props.model,
                    "voice": self.props.voice,
                    "input": self.props.text,
                    "response_format": self.props.response_format,
                    "speed": max(0.25, min(4.0, self.props.speed)),
                },
            )
            resp.raise_for_status()
            audio_bytes = resp.content

        fmt = self.props.response_format
        b64 = base64.b64encode(audio_bytes).decode()
        mime = {
            "mp3": "audio/mpeg",
            "opus": "audio/ogg",
            "aac": "audio/aac",
            "flac": "audio/flac",
            "wav": "audio/wav",
        }.get(fmt, "audio/mpeg")
        return NodeResult(
            success=True,
            output_data={
                "audio_base64": b64,
                "audio_data_uri": f"data:{mime};base64,{b64}",
                "format": fmt,
                "provider": "openai",
            },
        )

    async def _elevenlabs_tts(self, context: NodeContext) -> NodeResult:
        api_key = self._get_cred_key(
            context, "elevenlabs_api_key", self.props.elevenlabs_credential
        )
        if not api_key:
            return NodeResult(success=False, error="ElevenLabs credential required.")
        if not self.props.elevenlabs_voice_id.strip():
            return NodeResult(success=False, error="ElevenLabs Voice ID is required.")

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{self.props.elevenlabs_voice_id}",
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json={"text": self.props.text, "model_id": self.props.elevenlabs_model},
            )
            resp.raise_for_status()
            audio_bytes = resp.content

        b64 = base64.b64encode(audio_bytes).decode()
        return NodeResult(
            success=True,
            output_data={
                "audio_base64": b64,
                "audio_data_uri": f"data:audio/mpeg;base64,{b64}",
                "format": "mp3",
                "provider": "elevenlabs",
            },
        )

    def _get_cred_key(
        self, context: NodeContext, cred_type: str, selected_id: str | None
    ) -> str | None:
        credentials = context.credentials or []
        cred = None
        if selected_id:
            cred = next(
                (
                    c
                    for c in credentials
                    if str(c.get("id")) == str(selected_id) and c.get("type") == cred_type
                ),
                None,
            )
        if cred is None:
            cred = next((c for c in credentials if c.get("type") == cred_type), None)
        data = cred.get("data") if cred else None
        if not isinstance(data, dict):
            return None
        key = data.get("api_key")
        return key if isinstance(key, str) and key.strip() else None
