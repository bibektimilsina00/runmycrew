"""API-key credential provider for dropcontact.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="dropcontact_api_key",
    name="Dropcontact",
    icon_slug="dropcontact",
    color="#ffffff",
    description="Dropcontact — GDPR-friendly B2B email enrichment.",
    hint="Access token from Dropcontact settings",
    fields=[
        CredentialField(
            id="api_key",
            label="Access Token",
            type="password",
            placeholder="Dropcontact access token",
        ),
    ],
)
