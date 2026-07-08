"""API-key credential provider for confluence.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="confluence_api_key",
    name="Confluence",
    icon_slug="confluence",
    color="#ffffff",
    description="Confluence Cloud — pages, spaces, blogs, comments via REST v2",
    hint="https://yoursite.atlassian.net (same site as Jira)",
    fields=[
        CredentialField(
            id="email",
            label="Atlassian Email",
            type="text",
            placeholder="you@company.com",
        ),
        CredentialField(
            id="api_key",
            label="API Token",
            type="password",
            placeholder="ATATT3x...",
        ),
        CredentialField(
            id="base_url",
            label="Confluence Base URL",
            type="text",
            placeholder="https://yoursite.atlassian.net",
        ),
    ],
)
