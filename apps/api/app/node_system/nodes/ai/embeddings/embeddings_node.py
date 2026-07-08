from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.embeddings import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)


class EmbeddingsProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    model: str = "text-embedding-3-small"
    input: str = ""


class EmbeddingsNode(BaseNode[EmbeddingsProperties]):
    @classmethod
    def get_properties_model(cls) -> type[EmbeddingsProperties]:
        return EmbeddingsProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.embeddings",
            name=NAME,
            category="ai",
            description="Convert text to a vector embedding. Use with the Knowledge Base node or external vector stores.",
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "options",
                    "default": "openai",
                    "options": [
                        {"label": "OpenAI", "value": "openai"},
                        {"label": "Mistral", "value": "mistral"},
                        {"label": "Together AI", "value": "together"},
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
                            "mistral": "mistral_api_key",
                            "together": "together_api_key",
                        },
                    },
                },
                {
                    "name": "model",
                    "label": "Model",
                    "type": "options",
                    "default": "text-embedding-3-small",
                    "options": [
                        {
                            "label": "text-embedding-3-small (OpenAI, 1536d)",
                            "value": "text-embedding-3-small",
                        },
                        {
                            "label": "text-embedding-3-large (OpenAI, 3072d)",
                            "value": "text-embedding-3-large",
                        },
                        {
                            "label": "text-embedding-ada-002 (OpenAI, legacy)",
                            "value": "text-embedding-ada-002",
                        },
                        {"label": "mistral-embed (Mistral, 1024d)", "value": "mistral-embed"},
                        {
                            "label": "togethercomputer/m2-bert-80M-8k-retrieval",
                            "value": "togethercomputer/m2-bert-80M-8k-retrieval",
                        },
                    ],
                },
                {
                    "name": "input",
                    "label": "Text to Embed",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{$trigger.text}}",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "embedding", "type": "array"},
                {"label": "dimensions", "type": "number"},
                {"label": "model", "type": "string"},
                {"label": "tokens", "type": "object"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.input.strip():
            return NodeResult(success=False, error="Input text is required.")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error=f"{self.props.provider} credential required.")

        url, headers = self._provider_config(api_key)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json={"model": self.props.model, "input": self.props.input},
                )
                resp.raise_for_status()
                data = resp.json()

            embedding = data["data"][0]["embedding"]
            usage = data.get("usage") or {}
            return NodeResult(
                success=True,
                output_data={
                    "embedding": embedding,
                    "dimensions": len(embedding),
                    "model": data.get("model", self.props.model),
                    "tokens": {
                        "total_tokens": usage.get("total_tokens") or usage.get("prompt_tokens")
                    },
                },
            )

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"API error {e.response.status_code}: {e.response.text[:300]}"
            )
        except Exception as e:
            logger.error(f"EmbeddingsNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    def _provider_config(self, api_key: str) -> tuple[str, dict]:
        provider = self.props.provider
        if provider == "mistral":
            return "https://api.mistral.ai/v1/embeddings", {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        if provider == "together":
            return "https://api.together.ai/v1/embeddings", {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        return "https://api.openai.com/v1/embeddings", {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _get_api_key(self, context: NodeContext) -> str | None:
        type_map = {
            "openai": "openai_api_key",
            "mistral": "mistral_api_key",
            "together": "together_api_key",
        }
        cred_type = type_map.get(self.props.provider, "openai_api_key")
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
            return None
        key = data.get("api_key")
        return key if isinstance(key, str) and key.strip() else None
