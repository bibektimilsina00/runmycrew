"""API-key credential provider for fireworks.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="fireworks_api_key",
    name="Fireworks AI",
    icon_slug="fireworks",
    color="#ffffff",
    description="Fast serverless inference for open-weight models",
    hint="fw_...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="fw_...")],
    ai_provider_id="fireworks",
    default_model="accounts/fireworks/models/llama-v3p1-8b-instruct",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="openai_compatible",
    chat_completions_url="https://api.fireworks.ai/inference/v1/chat/completions",
    models_url="https://api.fireworks.ai/inference/v1/models",
)
