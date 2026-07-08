"""API-key credential provider for openrouter.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="openrouter_api_key",
    name="OpenRouter",
    icon_slug="openrouter",
    color="#1c1c1c",
    description="Access many model providers through the OpenRouter API",
    hint="sk-or-...",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="sk-or-...")
    ],
    ai_provider_id="openrouter",
    default_model="openai/gpt-4o-mini",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="openai_compatible",
    chat_completions_url="https://openrouter.ai/api/v1/chat/completions",
    models_url="https://openrouter.ai/api/v1/models",
)
