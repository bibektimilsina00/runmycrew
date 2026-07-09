"""MongoDB credential provider."""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mongodb_credentials",
    name="MongoDB",
    icon_slug="mongodb",
    color="#ffffff",
    description="MongoDB — connection string (mongodb+srv://…) or host + user + password.",
    hint="Paste the full connection string from Atlas, or fill the fields.",
    fields=[
        CredentialField(
            id="connectionString",
            label="Connection String",
            type="password",
            placeholder="mongodb+srv://user:pass@cluster0.mongodb.net/?retryWrites=true",
        ),
        CredentialField(id="host", label="Host (fallback)", type="string"),
        CredentialField(id="port", label="Port", type="string", placeholder="27017"),
        CredentialField(id="user", label="User", type="string"),
        CredentialField(id="password", label="Password", type="password"),
    ],
)
