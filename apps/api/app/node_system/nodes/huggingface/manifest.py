"""HuggingFace Inference action node — manifest form.

Targets the Hosted Inference API at `api-inference.huggingface.co`.
Each model lives at its own path (`/models/{model_id}`); the user picks
the model + sends the right `inputs` body shape for the task.

We expose three model categories as ops to make the inspector make
sense — they all hit the same endpoint, but with different body shapes
the user wants help building. Use `text-generation`, `summarization`,
or `text-classification` flavor depending on the model.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.huggingface",
    name="HuggingFace",
    category="integration",
    description=(
        "Run any model on the HuggingFace Hosted Inference API — "
        "text generation, summarization, classification, and more."
    ),
    icon_slug="huggingface",
    color="#ffffff",
    base_url="https://api-inference.huggingface.co",
    credential_type="huggingface_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="model_id",
            label="Model",
            type="string",
            required=True,
            placeholder="meta-llama/Llama-3.2-1B-Instruct",
            description=(
                "Full repo id from huggingface.co. Must support the Hosted Inference API."
            ),
        ),
        FieldSpec(
            name="inputs",
            label="Inputs",
            type="string",
            required=True,
            placeholder="Your prompt or text to classify…",
        ),
        FieldSpec(
            name="parameters",
            label="Parameters (JSON)",
            type="json",
            mode="advanced",
            placeholder='{"max_new_tokens": 256, "temperature": 0.7}',
        ),
        FieldSpec(
            name="options",
            label="Options (JSON)",
            type="json",
            mode="advanced",
            placeholder='{"wait_for_model": true, "use_cache": true}',
        ),
    ],
    operations=[
        OpSpec(
            id="text_generation",
            label="Text Generation",
            method="POST",
            path="/models/{model_id}",
            visible_fields=["model_id", "inputs", "parameters", "options"],
            body_fields=["inputs", "parameters", "options"],
        ),
        OpSpec(
            id="summarization",
            label="Summarization",
            method="POST",
            path="/models/{model_id}",
            visible_fields=["model_id", "inputs", "parameters", "options"],
            body_fields=["inputs", "parameters", "options"],
        ),
        OpSpec(
            id="text_classification",
            label="Text Classification",
            method="POST",
            path="/models/{model_id}",
            visible_fields=["model_id", "inputs", "options"],
            body_fields=["inputs", "options"],
        ),
        OpSpec(
            id="feature_extraction",
            label="Feature Extraction (Embeddings)",
            method="POST",
            path="/models/{model_id}",
            visible_fields=["model_id", "inputs", "options"],
            body_fields=["inputs", "options"],
        ),
    ],
    outputs_schema=[
        {"label": "generated_text", "type": "string"},
        {"label": "summary_text", "type": "string"},
        {"label": "label", "type": "string"},
        {"label": "score", "type": "number"},
        {"label": "embeddings", "type": "array"},
    ],
    allow_error=True,
)
