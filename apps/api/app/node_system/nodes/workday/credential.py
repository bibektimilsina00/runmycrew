"""API-key credential provider for workday.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="workday_api_key",
    name="Workday",
    icon_slug="workday",
    color="#ffffff",
    description="Workday — HR + finance ERP (RaaS + REST APIs).",
    hint="Workday API access",
    fields=[
        CredentialField(
            id="api_key",
            label="OAuth Access Token",
            type="password",
            placeholder="Workday token",
        ),
        CredentialField(
            id="tenant_url",
            label="Tenant URL",
            type="string",
            placeholder="https://xxx.workday.com",
        ),
        CredentialField(id="tenant", label="Tenant Name", type="string", placeholder="mycompany"),
    ],
)
