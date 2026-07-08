from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.perplexity import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"


class PerplexityProperties(BaseModel):
    credential: str | None = None
    model: str = "sonar"
    system_prompt: str | None = None
    query: str = ""
    temperature: float | None = None
    max_tokens: int | None = None
    search_recency_filter: str | None = None
    return_citations: bool = True


class PerplexityNode(BaseNode[PerplexityProperties]):
    @classmethod
    def get_properties_model(cls) -> type[PerplexityProperties]:
        return PerplexityProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.perplexity",
            name=NAME,
            category="ai",
            description="Search the web and get AI answers with live citations using Perplexity Sonar.",
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "credential",
                    "label": "Perplexity API Key",
                    "type": "credential",
                    "credentialType": "perplexity_api_key",
                    "required": True,
                },
                {
                    "name": "model",
                    "label": "Model",
                    "type": "options",
                    "default": "sonar",
                    "options": [
                        {"label": "Sonar (fast, web search)", "value": "sonar"},
                        {"label": "Sonar Pro (more thorough)", "value": "sonar-pro"},
                        {
                            "label": "Sonar Reasoning (thinking + search)",
                            "value": "sonar-reasoning",
                        },
                        {"label": "Sonar Deep Research", "value": "sonar-deep-research"},
                    ],
                },
                {
                    "name": "system_prompt",
                    "label": "System Prompt",
                    "type": "string",
                    "required": False,
                    "placeholder": "Be precise and concise.",
                },
                {
                    "name": "query",
                    "label": "Query",
                    "type": "string",
                    "required": True,
                    "placeholder": "What is the latest news on {{$trigger.topic}}?",
                },
                {
                    "name": "search_recency_filter",
                    "label": "Recency Filter",
                    "type": "options",
                    "required": False,
                    "options": [
                        {"label": "Any time", "value": ""},
                        {"label": "Past hour", "value": "hour"},
                        {"label": "Past day", "value": "day"},
                        {"label": "Past week", "value": "week"},
                        {"label": "Past month", "value": "month"},
                    ],
                    "mode": "advanced",
                },
                {
                    "name": "return_citations",
                    "label": "Return Citations",
                    "type": "boolean",
                    "default": True,
                    "mode": "advanced",
                },
                {
                    "name": "temperature",
                    "label": "Temperature",
                    "type": "number",
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
                {"label": "citations", "type": "array"},
                {"label": "model", "type": "string"},
                {"label": "tokens", "type": "object"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.query.strip():
            return NodeResult(success=False, error="Query is required.")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error="Perplexity API key required.")

        messages: list[dict] = []
        if self.props.system_prompt and self.props.system_prompt.strip():
            messages.append({"role": "system", "content": self.props.system_prompt.strip()})
        messages.append({"role": "user", "content": self.props.query})

        payload: dict[str, Any] = {"model": self.props.model, "messages": messages}
        if self.props.temperature is not None:
            payload["temperature"] = self.props.temperature
        if self.props.max_tokens is not None:
            payload["max_tokens"] = self.props.max_tokens
        if self.props.search_recency_filter:
            payload["search_recency_filter"] = self.props.search_recency_filter
        if self.props.return_citations:
            payload["return_citations"] = True

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    PERPLEXITY_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            choice = (data.get("choices") or [{}])[0]
            text = choice.get("message", {}).get("content") or ""
            citations = data.get("citations") or []
            usage = data.get("usage") or {}

            return NodeResult(
                success=True,
                output_data={
                    "text": text,
                    "citations": citations,
                    "model": data.get("model", self.props.model),
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                },
            )

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False,
                error=f"Perplexity API error {e.response.status_code}: {e.response.text[:300]}",
            )
        except Exception as e:
            logger.error(f"PerplexityNode failed: {e}", exc_info=True)
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
                    and c.get("type") == "perplexity_api_key"
                ),
                None,
            )
        if cred is None:
            cred = next((c for c in credentials if c.get("type") == "perplexity_api_key"), None)
        data = cred.get("data") if cred else None
        if not isinstance(data, dict):
            return None
        key = data.get("api_key")
        return key if isinstance(key, str) and key.strip() else None
