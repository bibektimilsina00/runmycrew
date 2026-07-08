"""API-key credential provider for anthropic.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="anthropic_api_key",
    name="Anthropic",
    icon_slug="anthropic",
    color="#ffffff",
    description="Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku",
    hint="sk-ant-...",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="sk-ant-...")
    ],
    ai_provider_id="anthropic",
    default_model="claude-3-5-sonnet-latest",
    supports_tools=True,
    supports_response_format=False,
    ai_api_type="anthropic",
    chat_completions_url="https://api.anthropic.com/v1/messages",
    models_url="https://api.anthropic.com/v1/models",
)
