"""API-key credential provider for wordpress.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="wordpress_api_key",
    name="WordPress",
    icon_slug="wordpress",
    color="#ffffff",
    description="WordPress — posts, pages, media (REST API).",
    hint="WordPress API access",
    fields=[
        CredentialField(
            id="username", label="WordPress Username", type="string", placeholder="admin"
        ),
        CredentialField(
            id="api_key",
            label="Application Password",
            type="password",
            placeholder="xxxx xxxx xxxx",
        ),
        CredentialField(id="site", label="Site domain", type="string", placeholder="myblog.com"),
    ],
)
