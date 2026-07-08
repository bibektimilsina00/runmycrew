"""API-key credential provider for greptile.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="greptile_api_key",
    name="Greptile",
    icon_slug="greptile",
    color="#ffffff",
    description="Greptile — natural-language code search over your repos.",
    hint="Greptile API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Greptile API key"
        ),
    ],
)
