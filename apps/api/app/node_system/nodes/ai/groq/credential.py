"""API-key credential provider for groq.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="groq_api_key",
    name="Groq",
    icon_slug="groq",
    color="#1c1c1c",
    description="Llama 3, Mixtral, Gemma (Ultra-fast inference)",
    hint="gsk-...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="gsk-...")],
    ai_provider_id="groq",
    default_model="llama-3.1-8b-instant",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="openai_compatible",
    chat_completions_url="https://api.groq.com/openai/v1/chat/completions",
    models_url="https://api.groq.com/openai/v1/models",
)
