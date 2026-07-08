"""API-key credential provider for servicenow.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="servicenow_api_key",
    name="ServiceNow",
    icon_slug="servicenow",
    color="#ffffff",
    description="ServiceNow — ITSM tickets, incidents, change requests via Table API.",
    hint="Instance + username + password",
    fields=[
        CredentialField(
            id="instance",
            label="Instance",
            type="string",
            placeholder="mycompany (from mycompany.service-now.com)",
        ),
        CredentialField(
            id="username",
            label="Username",
            type="string",
            placeholder="you@company.com",
        ),
        CredentialField(
            id="api_key",
            label="Password / API Token",
            type="password",
            placeholder="Password (or scoped OAuth token)",
        ),
    ],
)
