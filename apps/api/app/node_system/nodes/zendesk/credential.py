"""API-key credential provider for zendesk.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="zendesk_api_key",
    name="Zendesk",
    icon_slug="zendesk",
    color="#ffffff",
    description="Zendesk — tickets, users, orgs. Uses email/token Basic auth + per-subdomain URL.",
    hint="Subdomain + email + API token",
    fields=[
        CredentialField(
            id="subdomain",
            label="Subdomain",
            type="string",
            placeholder="mycompany (from mycompany.zendesk.com)",
        ),
        CredentialField(
            id="email",
            label="Agent Email",
            type="string",
            placeholder="you@company.com",
        ),
        CredentialField(
            id="api_key",
            label="API Token",
            type="password",
            placeholder="API Token",
        ),
    ],
)
