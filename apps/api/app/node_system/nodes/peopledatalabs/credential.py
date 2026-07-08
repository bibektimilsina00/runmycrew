"""API-key credential provider for peopledatalabs.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="peopledatalabs_api_key",
    name="People Data Labs",
    icon_slug="peopledatalabs",
    color="#1c1c1c",
    description="People Data Labs — person + company enrichment.",
    hint="API key from PDL dashboard",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="PDL API key",
        ),
    ],
)
