"""API-key credential provider for together.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="together_api_key",
    name="Together AI",
    icon_slug="together-ai",
    color="#1c1c1c",
    description="Open-source and hosted models through Together AI",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
    ai_provider_id="together",
    default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="openai_compatible",
    chat_completions_url="https://api.together.ai/v1/chat/completions",
    models_url="https://api.together.ai/v1/models",
)
