"""API-key credential provider for hex.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="hex_api_key",
    name="Hex",
    icon_slug="hex",
    color="#ffffff",
    description="Hex — collaborative data notebooks + apps.",
    hint="From Hex settings",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="Hex API key"),
    ],
)
