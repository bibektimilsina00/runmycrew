"""API-key credential provider for smtp.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="smtp_credentials",
    name="SMTP",
    icon_slug="smtp",
    color="#1c1c1c",
    description="Send email via any SMTP server (STARTTLS / SSL / plain).",
    hint="SMTP host, port, credentials",
    fields=[
        CredentialField(id="host", label="Host", type="string", placeholder="smtp.example.com"),
        CredentialField(id="port", label="Port", type="number", placeholder="587"),
        CredentialField(
            id="username", label="Username", type="string", placeholder="user@example.com"
        ),
        CredentialField(
            id="password", label="Password", type="password", placeholder="app password"
        ),
        CredentialField(
            id="encryption",
            label="Encryption (starttls|ssl|none, placeholder=)",
            type="string",
            placeholder="starttls",
        ),
        CredentialField(
            id="from_address",
            label="Default From Address",
            type="string",
            placeholder="noreply@example.com",
        ),
    ],
)
