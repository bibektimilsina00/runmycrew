"""API-key credential provider for grafana.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="grafana_api_key",
    name="Grafana Cloud",
    icon_slug="grafana",
    color="#ffffff",
    description="Grafana Cloud — dashboards, alerts, annotations, folders.",
    hint="From Grafana Cloud settings",
    fields=[
        CredentialField(
            id="api_key", label="Service Account Token", type="password", placeholder="glsa_..."
        ),
        CredentialField(
            id="stack", label="Stack subdomain", type="string", placeholder="mycompany"
        ),
    ],
)
