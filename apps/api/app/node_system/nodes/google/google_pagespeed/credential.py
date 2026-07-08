"""API-key credential provider for google_pagespeed.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="google_pagespeed_api_key",
    name="Google PageSpeed Insights",
    icon_slug="google_pagespeed",
    color="#ffffff",
    description="PageSpeed Insights — Lighthouse audits for a URL.",
    hint="Google PageSpeed Insights API key",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Google PageSpeed Insights API key",
        ),
    ],
)
