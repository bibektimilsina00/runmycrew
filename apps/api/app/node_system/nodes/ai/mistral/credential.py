"""API-key credential provider for mistral.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mistral_api_key",
    name="Mistral AI",
    icon_slug="mistral",
    color="#ffffff",
    description="Mistral chat and code models",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
    ai_provider_id="mistral",
    default_model="mistral-small-latest",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="openai_compatible",
    chat_completions_url="https://api.mistral.ai/v1/chat/completions",
    models_url="https://api.mistral.ai/v1/models",
)
