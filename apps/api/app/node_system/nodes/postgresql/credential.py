"""API-key credential provider for postgresql.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="postgresql_credentials",
    name="PostgreSQL",
    icon_slug="postgresql",
    color="#ffffff",
    description="PostgreSQL — connection info for asyncpg.",
    hint="host / port / user / password / database",
    fields=[
        CredentialField(id="host", label="Host", type="string", placeholder="db.example.com"),
        CredentialField(id="port", label="Port", type="number", placeholder="5432"),
        CredentialField(id="user", label="User", type="string", placeholder="postgres"),
        CredentialField(id="password", label="Password", type="password"),
        CredentialField(id="database", label="Database", type="string", placeholder="myapp"),
        CredentialField(
            id="ssl",
            label="SSL Mode (prefer|require|disable)",
            type="string",
            placeholder="prefer",
        ),
    ],
)
