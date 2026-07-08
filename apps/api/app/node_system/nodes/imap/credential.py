"""API-key credential provider for imap.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="imap_creds",
    name="IMAP Email",
    icon_slug="mail",
    color="#ffffff",
    description="Generic IMAP mailbox — Gmail, Outlook, Yahoo, self-hosted. App-password for Gmail.",
    hint="Host + port + username + password",
    fields=[
        CredentialField(
            id="host",
            label="IMAP Host",
            type="string",
            placeholder="imap.gmail.com",
        ),
        CredentialField(
            id="port",
            label="Port",
            type="string",
            placeholder="993 (IMAPS) or 143 (STARTTLS)",
        ),
        CredentialField(
            id="username",
            label="Username",
            type="string",
            placeholder="you@example.com",
        ),
        CredentialField(
            id="password",
            label="Password / App Password",
            type="password",
            placeholder="App-password (Gmail / Outlook 2FA)",
        ),
        CredentialField(
            id="use_ssl",
            label="Use SSL (true/false, placeholder=)",
            type="string",
            placeholder="true",
        ),
    ],
)
