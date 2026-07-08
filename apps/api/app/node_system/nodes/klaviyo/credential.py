"""API-key credential provider for klaviyo.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="klaviyo_api_key",
    name="Klaviyo",
    icon_slug="klaviyo",
    color="#ffffff",
    description="Klaviyo — email + SMS marketing, profiles, events.",
    hint="Private API Key (pk_...)",
    fields=[
        CredentialField(
            id="api_key", label="Private API Key", type="password", placeholder="pk_..."
        )
    ],
)
