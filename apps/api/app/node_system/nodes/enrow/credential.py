"""API-key credential provider for enrow.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="enrow_api_key",
    name="Enrow",
    icon_slug="enrow",
    color="#ffffff",
    description="Enrow — waterfall B2B email finder + verifier.",
    hint="API key from Enrow dashboard",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Enrow API key",
        ),
    ],
)
