"""API-key credential provider for incidentio.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="incidentio_api_key",
    name="incident.io",
    icon_slug="incidentio",
    color="#ffffff",
    description="incident.io — incident response + postmortems.",
    hint="incident.io API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="incident.io API key"
        ),
    ],
)
