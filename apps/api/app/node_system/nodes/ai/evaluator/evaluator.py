from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

import httpx
from pydantic import BaseModel, Field

from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.api_keys import get_ai_provider, get_ai_providers
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.evaluator import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)


class EvaluatorMetric(BaseModel):
    name: str
    description: str = ""
    min: float = 0
    max: float = 10


class EvaluatorProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    openaiCredential: str | None = None
    anthropicCredential: str | None = None
    googleCredential: str | None = None
    groqCredential: str | None = None
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
            name=NAME,
            category="ai",
            description="Use an LLM to score content against defined metrics.",
            icon=ICON_SLUG,
            color=COLOR,
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
                    "placeholder": "Type or select a model ID",
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
                    "name": "content",
                    "label": "Content to Evaluate",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{$step.content}}",
                },
                {
                    "name": "metrics",
                    "label": "Metrics",
                    "type": "collection",
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
                    "typeOptions": {
                        "multipleValues": True,
                        "addButtonText": "Add metric",
                        "autoIncrementField": "name",
                        "autoIncrementPrefix": "metric",
                    },
                    "properties": [
                        {
                            "name": "name",
                            "label": "Name",
                            "type": "string",
                            "placeholder": "correctness",
                            "required": True,
                        },
                        {
                            "name": "description",
                            "label": "Description",
                            "type": "string",
                            "placeholder": "What does this metric measure?",
                        },
                        {"name": "min", "label": "Min", "type": "number", "default": 0},
                        {"name": "max", "label": "Max", "type": "number", "default": 10},
                    ],
                    "description": "Score the content on each metric (name, description, min–max range).",
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

    @classmethod
    def _provider_credential_properties(cls) -> list[dict[str, Any]]:
        credential_properties = [
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
        catalog_by_provider = {provider.ai_provider_id: provider for provider in get_ai_providers()}
        for prop in credential_properties:
            provider_id = prop["condition"]["value"]
            catalog_provider = catalog_by_provider.get(provider_id)
            if catalog_provider:
                prop["label"] = f"{catalog_provider.name} API Key"
                prop["credentialType"] = catalog_provider.id
            prop["visibility"] = "hidden"
        return credential_properties

    @classmethod
    def _credential_type_by_provider(cls) -> dict[str, str]:
        return {
            provider.ai_provider_id: provider.id
            for provider in get_ai_providers()
            if provider.ai_provider_id
        }

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

            output: dict[str, Any] = {
                "scores": scores,
                "passed": result.get("passed", average >= (max_total / len(metrics)) * 0.6),
                "feedback": result.get("feedback", ""),
                "average": round(average, 2),
            }
            # Pass the judged artifact through — the evaluator often
            # terminates a crew round, and without this the maker's
            # content dies at the verdict (hosted chat had nothing to say).
            if self.props.content:
                output["content"] = self.props.content
            return NodeResult(success=True, output_data=output)
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
