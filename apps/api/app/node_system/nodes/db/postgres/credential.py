"""Postgres credential provider.

Stores a full connection string (recommended) OR host + port + user +
password + database as separate fields. The picker lookups + node
runtime both accept either shape.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="postgres_credentials",
    name="PostgreSQL",
    icon_slug="postgres",
    color="#ffffff",
    description="PostgreSQL — connection string or host/port/user/password/db.",
    hint="Paste a full connection string (postgresql://user:pass@host:port/db) or fill the fields below.",
    fields=[
        CredentialField(
            id="connectionString",
            label="Connection String",
            type="password",
            placeholder="postgresql://user:pass@host:5432/db",
        ),
        CredentialField(id="host", label="Host (fallback)", type="string", placeholder="localhost"),
        CredentialField(id="port", label="Port", type="string", placeholder="5432"),
        CredentialField(id="user", label="User", type="string", placeholder="postgres"),
        CredentialField(id="password", label="Password", type="password"),
        CredentialField(id="database", label="Database", type="string", placeholder="postgres"),
    ],
)
