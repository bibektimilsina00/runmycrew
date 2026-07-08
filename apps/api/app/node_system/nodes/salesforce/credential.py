"""API-key credential provider for salesforce.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="salesforce_api_key",
    name="Salesforce",
    icon_slug="salesforce",
    color="#ffffff",
    description="Salesforce — CRM records via Connected App access token",
    hint="Access token from Salesforce Connected App",
    fields=[
        CredentialField(id="api_key", label="Access Token", type="password", placeholder="00D..."),
        CredentialField(
            id="instance_url",
            label="Instance URL",
            type="text",
            placeholder="https://yourorg.my.salesforce.com",
        ),
    ],
)
