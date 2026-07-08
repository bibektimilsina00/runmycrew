"""HubSpot polling trigger — manifest form.

Watches CRM objects (contacts, companies, deals, tickets) for new
records via HubSpot's search endpoints. Bearer auth (works for both
Private App tokens and OAuth access tokens — hubspot_node upgraded
to accept both credential types in Phase 2.2).
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.hubspot import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_crm(item):
    props = item.get("properties") or {}
    return {
        "id": item.get("id"),
        "createdAt": item.get("createdAt"),
        "updatedAt": item.get("updatedAt"),
        "email": props.get("email"),
        "firstname": props.get("firstname"),
        "lastname": props.get("lastname"),
        "name": props.get("name"),
        "dealname": props.get("dealname"),
        "subject": props.get("subject"),
        "properties": props,
    }


register_flatten("hubspot.crm", _flatten_crm)


MANIFEST = PollingTriggerManifest(
    type="trigger.hubspot",
    name=NAME,
    description="Poll HubSpot for new contacts, companies, deals, or tickets.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.hubapi.com",
    credential_type=["hubspot_oauth", "hubspot_api_key"],
    token_field=["access_token", "api_key"],
    auth="bearer",
    provider="hubspot",
    default_poll_interval_seconds=120,
    common_fields=[
        FieldSpec(
            name="limit",
            label="Limit",
            type="number",
            default=50,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_contact",
            label="New Contact",
            list_path="/crm/v3/objects/contacts",
            list_params={"limit": "{limit}", "sort": "-createdate"},
            strategy="known_ids",
            id_field="id",
            flatten="hubspot.crm",
        ),
        PollingEvent(
            id="new_company",
            label="New Company",
            list_path="/crm/v3/objects/companies",
            list_params={"limit": "{limit}", "sort": "-createdate"},
            strategy="known_ids",
            id_field="id",
            flatten="hubspot.crm",
        ),
        PollingEvent(
            id="new_deal",
            label="New Deal",
            list_path="/crm/v3/objects/deals",
            list_params={"limit": "{limit}", "sort": "-createdate"},
            strategy="known_ids",
            id_field="id",
            flatten="hubspot.crm",
        ),
        PollingEvent(
            id="new_ticket",
            label="New Ticket",
            list_path="/crm/v3/objects/tickets",
            list_params={"limit": "{limit}", "sort": "-createdate"},
            strategy="known_ids",
            id_field="id",
            flatten="hubspot.crm",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "createdAt", "type": "string"},
        {"label": "updatedAt", "type": "string"},
        {"label": "properties", "type": "object"},
    ],
)
