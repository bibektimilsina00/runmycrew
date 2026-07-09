"""MySQL credential provider."""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mysql_credentials",
    name="MySQL",
    icon_slug="mysql",
    color="#ffffff",
    description="MySQL — connection string or host/port/user/password/db.",
    hint="Full connection string (mysql://user:pass@host:port/db) or fill fields below.",
    fields=[
        CredentialField(
            id="connectionString",
            label="Connection String",
            type="password",
            placeholder="mysql://user:pass@host:3306/db",
        ),
        CredentialField(id="host", label="Host (fallback)", type="string", placeholder="localhost"),
        CredentialField(id="port", label="Port", type="string", placeholder="3306"),
        CredentialField(id="user", label="User", type="string", placeholder="root"),
        CredentialField(id="password", label="Password", type="password"),
        CredentialField(id="database", label="Database", type="string"),
    ],
)
