"""API-key credential provider for openai.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="openai_api_key",
    name="OpenAI",
    icon_slug="openai",
    color="#1c1c1c",
    description="Use your OpenAI API key for AI nodes",
    hint="sk-...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="sk-...")],
    ai_provider_id="openai",
    default_model="gpt-4o-mini",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="openai_compatible",
    chat_completions_url="https://api.openai.com/v1/chat/completions",
    models_url="https://api.openai.com/v1/models",
)
