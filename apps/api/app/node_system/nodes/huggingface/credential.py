"""API-key credential provider for huggingface.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="huggingface_api_key",
    name="HuggingFace",
    icon_slug="huggingface",
    color="#ffffff",
    description="HuggingFace Hosted Inference — run any model from the Hub.",
    hint="hf_...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="hf_...")],
)
