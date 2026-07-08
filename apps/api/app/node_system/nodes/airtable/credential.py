"""API-key credential provider for airtable.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="airtable_api_key",
    name="Airtable",
    icon_slug="airtable",
    color="#ffffff",
    description="Airtable — database and spreadsheet automation",
    hint="pat...",
    fields=[
        CredentialField(
            id="api_key", label="Personal Access Token", type="password", placeholder="pat..."
        )
    ],
)
