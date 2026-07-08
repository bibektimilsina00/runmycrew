"""API-key credential provider for icypeas.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="icypeas_api_key",
    name="Icypeas",
    icon_slug="icypeas",
    color="#ffffff",
    description="Icypeas — email finder + LinkedIn enrichment.",
    hint="API key from Icypeas dashboard",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Icypeas API key",
        ),
    ],
)
