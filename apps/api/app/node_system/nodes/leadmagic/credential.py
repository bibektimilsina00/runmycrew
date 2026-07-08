"""API-key credential provider for leadmagic.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="leadmagic_api_key",
    name="LeadMagic",
    icon_slug="leadmagic",
    color="#ffffff",
    description="LeadMagic — email finder + waterfall enrichment.",
    hint="API key from LeadMagic dashboard",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="LeadMagic API key",
        ),
    ],
)
