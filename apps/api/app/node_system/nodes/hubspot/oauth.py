from __future__ import annotations

from apps.api.app.credential_manager.oauth.base import (
    _SimpleOAuthProvider,
)


class HubSpotOAuthProvider(_SimpleOAuthProvider):
    id = "hubspot_oauth"
    name = "HubSpot (OAuth)"
    icon_slug = "hubspot"
    color = "#1c1c1c"
    description = "Connect HubSpot CRM via OAuth — contacts, deals, companies, tickets."
    scopes = [
        "Read and write CRM contacts, companies, deals, and tickets",
        "Send transactional emails and manage marketing assets",
        "Read your HubSpot account profile",
    ]
    _AUTH_URL = "https://app.hubspot.com/oauth/authorize"
    _TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
    _SCOPE_STR = (
        "crm.objects.contacts.read crm.objects.contacts.write "
        "crm.objects.companies.read crm.objects.companies.write "
        "crm.objects.deals.read crm.objects.deals.write tickets oauth"
    )
    _CLIENT_ID_ATTR = "HUBSPOT_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "HUBSPOT_CLIENT_SECRET"
    _REDIRECT_SERVICE = "hubspot"


PROVIDER = HubSpotOAuthProvider()
