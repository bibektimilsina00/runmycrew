"""Neo4j credential provider."""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="neo4j_credentials",
    name="Neo4j",
    icon_slug="neo4j",
    color="#ffffff",
    description="Neo4j — Aura connection URI + user + password.",
    hint="URI (bolt+s://…) + user + password from Aura or self-hosted.",
    fields=[
        CredentialField(
            id="uri",
            label="URI",
            type="string",
            placeholder="neo4j+s://xxxx.databases.neo4j.io",
        ),
        CredentialField(id="user", label="User", type="string", placeholder="neo4j"),
        CredentialField(id="password", label="Password", type="password"),
    ],
)
