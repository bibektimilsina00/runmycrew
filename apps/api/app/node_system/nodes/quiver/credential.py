"""API-key credential provider for quiver.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="quiver_api_key",
    name="Quiver Quantitative",
    icon_slug="quiver",
    color="#ffffff",
    description="Quiver — congressional trades, lobbying, WSB, gov contracts.",
    hint="Quiver Quantitative API key",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Quiver Quantitative API key",
        ),
    ],
)
