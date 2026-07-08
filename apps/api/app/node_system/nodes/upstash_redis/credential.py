"""API-key credential provider for upstash_redis.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="upstash_redis_api_key",
    name="Upstash Redis",
    icon_slug="upstash",
    color="#ffffff",
    description="Upstash Redis — REST-driven Redis commands.",
    hint="REST URL + REST token",
    fields=[
        CredentialField(
            id="rest_url",
            label="REST URL",
            type="string",
            placeholder="https://abc-12345.upstash.io",
        ),
        CredentialField(id="api_key", label="REST Token", type="password", placeholder="Token"),
    ],
)
