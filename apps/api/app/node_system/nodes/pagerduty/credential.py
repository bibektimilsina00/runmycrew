"""API-key credential provider for pagerduty.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="pagerduty_api_key",
    name="PagerDuty",
    icon_slug="pagerduty",
    color="#ffffff",
    description="PagerDuty — incidents, services, on-call.",
    hint="REST API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
