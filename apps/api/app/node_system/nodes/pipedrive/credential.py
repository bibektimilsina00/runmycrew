"""API-key credential provider for pipedrive.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="pipedrive_api_key",
    name="Pipedrive",
    icon_slug="pipedrive",
    color="#ffffff",
    description="Pipedrive CRM — deals, persons, organizations.",
    hint="API token + company domain",
    fields=[
        CredentialField(
            id="company_domain",
            label="Company Domain",
            type="string",
            placeholder="your-team",
        ),
        CredentialField(id="api_key", label="API Token", type="password", placeholder="Token"),
    ],
)
