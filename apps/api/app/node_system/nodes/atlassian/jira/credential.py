"""API-key credential provider for jira.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="jira_api_key",
    name="Jira",
    icon_slug="jira",
    color="#ffffff",
    description="Jira — project management and issue tracking via REST API v3",
    hint="https://yoursite.atlassian.net",
    fields=[
        CredentialField(
            id="email", label="Atlassian Email", type="text", placeholder="you@company.com"
        ),
        CredentialField(id="api_key", label="API Token", type="password", placeholder="ATATT3x..."),
        CredentialField(
            id="base_url",
            label="Jira Base URL",
            type="text",
            placeholder="https://yoursite.atlassian.net",
        ),
    ],
)
