"""API-key credential provider for stripe.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="stripe_api_key",
    name="Stripe",
    icon_slug="stripe",
    color="#ffffff",
    description="Stripe — payments and billing automation",
    hint="sk_live_... or sk_test_...",
    fields=[
        CredentialField(
            id="api_key", label="Secret Key", type="password", placeholder="sk_live_..."
        )
    ],
)
