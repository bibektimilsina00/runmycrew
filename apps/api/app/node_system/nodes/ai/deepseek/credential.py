"""API-key credential provider for deepseek.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="deepseek_api_key",
    name="DeepSeek",
    icon_slug="deepseek",
    color="#ffffff",
    description="DeepSeek chat and reasoning models",
    hint="sk-...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="sk-...")],
    ai_provider_id="deepseek",
    default_model="deepseek-chat",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="openai_compatible",
    chat_completions_url="https://api.deepseek.com/chat/completions",
    models_url="https://api.deepseek.com/models",
)
