"""API-key credential provider for shopify.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="shopify_api_key",
    name="Shopify",
    icon_slug="shopify",
    color="#ffffff",
    description="Shopify Admin — orders, products, customers.",
    hint="Admin API access token + store domain",
    fields=[
        CredentialField(
            id="store_domain",
            label="Store Domain",
            type="string",
            placeholder="your-store (without .myshopify.com)",
        ),
        CredentialField(
            id="api_key", label="Access Token", type="password", placeholder="shpat_..."
        ),
    ],
)
