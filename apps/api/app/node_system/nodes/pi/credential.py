"""API-key credential provider for pi.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="pi_api_key",
    name="Pi",
    icon_slug="pi",
    color="#1c1c1c",
    description="Pi — Inflection AI conversational assistant.",
    hint="Pi API access",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="Pi API key"),
    ],
)
