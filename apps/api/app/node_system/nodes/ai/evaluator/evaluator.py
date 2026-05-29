from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

import httpx
from pydantic import BaseModel, Field

from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.api_keys import get_ai_provider
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class EvaluatorMetric(BaseModel):
    name: str
    description: str = ""
    min: float = 0
    max: float = 10


class EvaluatorProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    model: str | None = None
    content: str = ""
    metrics: list[EvaluatorMetric] | str = Field(default_factory=list)
    temperature: float = 0.0


class EvaluatorNode(BaseNode[EvaluatorProperties]):
    @classmethod
    def get_properties_model(cls) -> type[EvaluatorProperties]:
        return EvaluatorProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.evaluator",
            name="Evaluator",
            category="ai",
            description="Use an LLM to score content against defined metrics.",
            icon="BarChart2",
            color="#f59e0b",
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "string",
                    "default": "openai",
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
                    "type": "string",
                    "required": True,
                    "loadOptions": "/ai/models",
                    "loadOptionsDependsOn": ["provider", "credential"],
                },
                {
                    "name": "content",
                    "label": "Content to Evaluate",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{previous_node.output.content}}",
                },
                {
                    "name": "metrics",
                    "label": "Metrics",
                    "type": "json",
                    "required": True,
                    "default": [
                        {
                            "name": "relevance",
                            "description": "How relevant is the content?",
                            "min": 0,
                            "max": 10,
                        },
                        {
                            "name": "clarity",
                            "description": "How clear and readable?",
                            "min": 0,
                            "max": 10,
                        },
                    ],
                    "description": "Array of {name, description, min, max} metrics.",
                },
                {
                    "name": "temperature",
                    "label": "Temperature",
                    "type": "number",
                    "default": 0.0,
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "scores", "type": "object"},
                {"label": "passed", "type": "boolean"},
                {"label": "feedback", "type": "string"},
                {"label": "average", "type": "number"},
            ],
            allow_error=True,
        )

    def _parse_metrics(self) -> list[EvaluatorMetric]:
        raw = self.props.metrics
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return []
        if not isinstance(raw, list):
            return []
        metrics = []
        for item in raw:
            if isinstance(item, EvaluatorMetric):
                metrics.append(item)
            elif isinstance(item, dict):
                with suppress(Exception):
                    metrics.append(EvaluatorMetric(**item))
        return metrics

    def _build_prompt(self, metrics: list[EvaluatorMetric]) -> tuple[str, dict[str, Any]]:
        metric_lines = "\n".join(f"- {m.name} ({m.min}–{m.max}): {m.description}" for m in metrics)
        system = (
            "You are an objective evaluator. Score the provided content on each metric "
            "and return a JSON object with exactly the keys listed. "
            "Also include 'feedback' (string) with brief reasoning and 'passed' (bool) "
            "indicating if average score >= 60% of max.\n\n"
            f"Metrics:\n{metric_lines}"
        )

        response_schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "feedback": {"type": "string"},
                "passed": {"type": "boolean"},
                **{
                    m.name: {
                        "type": "number",
                        "description": f"Score between {m.min} and {m.max}",
                    }
                    for m in metrics
                },
            },
            "required": ["feedback", "passed", *[m.name for m in metrics]],
            "additionalProperties": False,
        }
        return system, response_schema

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        metrics = self._parse_metrics()
        if not metrics:
            return NodeResult(success=False, error="At least one metric is required.")
        if not self.props.content.strip():
            return NodeResult(success=False, error="Content is required.")

        ai_provider = get_ai_provider(self.props.provider)
        if not ai_provider:
            return NodeResult(success=False, error=f"Unknown provider: {self.props.provider}")

        api_key = self._get_api_key(context)
        if not api_key:
            return NodeResult(success=False, error=f"{ai_provider.name} credential required.")

        system_prompt, response_schema = self._build_prompt(metrics)
        model = self.props.model or (ai_provider.default_model if ai_provider.default_model else "")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.props.content},
        ]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if ai_provider.ai_api_type in ("openai_compatible",):
                    payload: dict[str, Any] = {
                        "model": model,
                        "messages": messages,
                        "temperature": self.props.temperature,
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "evaluation",
                                "schema": response_schema,
                                "strict": True,
                            },
                        },
                    }
                    response = await client.post(
                        ai_provider.chat_completions_url or "",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    raw_content = data["choices"][0]["message"]["content"]
                else:
                    return NodeResult(
                        success=False, error="Evaluator supports openai_compatible providers only."
                    )

            result = json.loads(raw_content)
            scores = {m.name: result.get(m.name, m.min) for m in metrics}
            total = sum(scores.values())
            max_total = sum(m.max for m in metrics)
            average = total / len(metrics) if metrics else 0

            return NodeResult(
                success=True,
                output_data={
                    "scores": scores,
                    "passed": result.get("passed", average >= (max_total / len(metrics)) * 0.6),
                    "feedback": result.get("feedback", ""),
                    "average": round(average, 2),
                },
            )
        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"API error {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))

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
