"""API-key credential provider for jira_service_management.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="jira_service_management_api_key",
    name="Jira Service Management",
    icon_slug="jira",
    color="#ffffff",
    description="Jira Service Management — requests, service desks, queues.",
    hint="Atlassian email + API token",
    fields=[
        CredentialField(
            id="email", label="Atlassian Email", type="string", placeholder="you@example.com"
        ),
        CredentialField(id="api_key", label="API Token", type="password", placeholder="ATATT..."),
        CredentialField(
            id="domain",
            label="Atlassian Domain",
            type="string",
            placeholder="mycompany.atlassian.net",
        ),
    ],
)
