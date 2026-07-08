"""API-key credential provider for xai.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="xai_api_key",
    name="xAI",
    icon_slug="xai",
    color="#ffffff",
    description="Grok models from xAI",
    hint="xai-...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="xai-...")],
    ai_provider_id="xai",
    default_model="grok-4",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="openai_compatible",
    chat_completions_url="https://api.x.ai/v1/chat/completions",
    models_url="https://api.x.ai/v1/models",
)
