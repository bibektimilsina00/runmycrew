"""HubSpot action node — manifest form.

HubSpot CRM v3 API at `https://api.hubapi.com`. Bearer auth from
either OAuth (`access_token`) or a private-app token (`api_key`).

Refactored from a custom BaseNode. Existing 10 op names preserved:
list_contacts, get_contact, create_contact, update_contact,
search_contacts, create_deal, get_deal, list_deals, create_company,
list_companies. Adds 30+ new ops toward sim's 38-op parity.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest


def _contact_props(v):  # noqa: ANN001
    return {
        k: val
        for k, val in {
            "email": getattr(v, "email", None) or None,
            "firstname": getattr(v, "first_name", None) or None,
            "lastname": getattr(v, "last_name", None) or None,
            "phone": getattr(v, "phone", None) or None,
            "company": getattr(v, "company_name", None) or None,
        }.items()
        if val is not None
    }


MANIFEST = ProviderManifest(
    type="action.hubspot",
    name="HubSpot",
    category="integration",
    description="HubSpot — contacts, companies, deals, tickets, engagements, lists.",
    icon_slug="hubspot",
    color="#FF7A59",
    base_url="https://api.hubapi.com",
    credential_type=["hubspot_oauth", "hubspot_api_key"],
    token_field=["access_token", "api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="contact_id", label="Contact ID", type="string"),
        FieldSpec(name="deal_id", label="Deal ID", type="string"),
        FieldSpec(name="company_id", label="Company ID", type="string"),
        FieldSpec(name="ticket_id", label="Ticket ID", type="string"),
        FieldSpec(name="engagement_id", label="Engagement ID", type="string"),
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="owner_id", label="Owner ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="phone", label="Phone", type="string"),
        FieldSpec(name="company_name", label="Company Name", type="string"),
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="deal_name", label="Deal Name", type="string"),
        FieldSpec(name="deal_stage", label="Deal Stage", type="string"),
        FieldSpec(name="deal_amount", label="Deal Amount", type="number"),
        FieldSpec(name="pipeline", label="Pipeline", type="string"),
        FieldSpec(name="ticket_name", label="Ticket Name", type="string"),
        FieldSpec(name="ticket_pipeline", label="Ticket Pipeline", type="string"),
        FieldSpec(name="ticket_stage", label="Ticket Stage", type="string"),
        FieldSpec(name="ticket_content", label="Ticket Content", type="string"),
        FieldSpec(name="ticket_priority", label="Ticket Priority", type="string"),
        FieldSpec(
            name="engagement_type",
            label="Engagement Type (NOTE|EMAIL|CALL|MEETING|TASK)",
            type="string",
            default="NOTE",
        ),
        FieldSpec(name="engagement_body", label="Engagement Body", type="string"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(name="properties_body", label="Properties (JSON)", type="json", default={}),
        FieldSpec(name="associations_body", label="Associations (JSON)", type="json", default=[]),
        FieldSpec(name="from_object_id", label="From Object ID", type="string"),
        FieldSpec(name="to_object_id", label="To Object ID", type="string"),
        FieldSpec(name="association_type", label="Association Type", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=20, mode="advanced"),
        FieldSpec(name="after", label="After (paging cursor)", type="string", mode="advanced"),
    ],
    operations=[
        # ─── contacts (legacy + depth) ─────────────────────────────
        OpSpec(
            id="list_contacts",
            label="List Contacts",
            method="GET",
            path="/crm/v3/objects/contacts",
            visible_fields=["limit", "after"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "limit": int(getattr(v, "limit", 20) or 20),
                    "after": getattr(v, "after", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_contact",
            label="Get Contact",
            method="GET",
            path="/crm/v3/objects/contacts/{contact_id}",
            visible_fields=["contact_id"],
        ),
        OpSpec(
            id="create_contact",
            label="Create Contact",
            method="POST",
            path="/crm/v3/objects/contacts",
            visible_fields=["email", "first_name", "last_name", "phone", "company_name"],
            body_builder=lambda v: {"properties": _contact_props(v)},
        ),
        OpSpec(
            id="update_contact",
            label="Update Contact",
            method="PATCH",
            path="/crm/v3/objects/contacts/{contact_id}",
            visible_fields=["contact_id", "email", "first_name", "last_name", "phone"],
            body_builder=lambda v: {"properties": _contact_props(v)},
        ),
        OpSpec(
            id="search_contacts",
            label="Search Contacts",
            method="POST",
            path="/crm/v3/objects/contacts/search",
            visible_fields=["query", "limit"],
            body_builder=lambda v: {
                "query": getattr(v, "query", None) or "",
                "limit": int(getattr(v, "limit", 20) or 20),
            },
        ),
        OpSpec(
            id="delete_contact",
            label="Delete Contact",
            method="DELETE",
            path="/crm/v3/objects/contacts/{contact_id}",
            visible_fields=["contact_id"],
        ),
        # ─── deals (legacy + depth) ────────────────────────────────
        OpSpec(
            id="create_deal",
            label="Create Deal",
            method="POST",
            path="/crm/v3/objects/deals",
            visible_fields=["deal_name", "deal_stage", "deal_amount", "pipeline"],
            body_builder=lambda v: {
                "properties": {
                    k: val
                    for k, val in {
                        "dealname": getattr(v, "deal_name", None) or None,
                        "dealstage": getattr(v, "deal_stage", None) or None,
                        "amount": getattr(v, "deal_amount", None) or None,
                        "pipeline": getattr(v, "pipeline", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="get_deal",
            label="Get Deal",
            method="GET",
            path="/crm/v3/objects/deals/{deal_id}",
            visible_fields=["deal_id"],
        ),
        OpSpec(
            id="list_deals",
            label="List Deals",
            method="GET",
            path="/crm/v3/objects/deals",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 20) or 20)},
        ),
        OpSpec(
            id="update_deal",
            label="Update Deal",
            method="PATCH",
            path="/crm/v3/objects/deals/{deal_id}",
            visible_fields=["deal_id", "deal_name", "deal_stage", "deal_amount"],
            body_builder=lambda v: {
                "properties": {
                    k: val
                    for k, val in {
                        "dealname": getattr(v, "deal_name", None) or None,
                        "dealstage": getattr(v, "deal_stage", None) or None,
                        "amount": getattr(v, "deal_amount", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="delete_deal",
            label="Delete Deal",
            method="DELETE",
            path="/crm/v3/objects/deals/{deal_id}",
            visible_fields=["deal_id"],
        ),
        OpSpec(
            id="search_deals",
            label="Search Deals",
            method="POST",
            path="/crm/v3/objects/deals/search",
            visible_fields=["query", "limit"],
            body_builder=lambda v: {
                "query": getattr(v, "query", None) or "",
                "limit": int(getattr(v, "limit", 20) or 20),
            },
        ),
        # ─── companies ─────────────────────────────────────────────
        OpSpec(
            id="create_company",
            label="Create Company",
            method="POST",
            path="/crm/v3/objects/companies",
            visible_fields=["company_name", "domain"],
            body_builder=lambda v: {
                "properties": {
                    k: val
                    for k, val in {
                        "name": getattr(v, "company_name", None) or None,
                        "domain": getattr(v, "domain", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="list_companies",
            label="List Companies",
            method="GET",
            path="/crm/v3/objects/companies",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 20) or 20)},
        ),
        OpSpec(
            id="get_company",
            label="Get Company",
            method="GET",
            path="/crm/v3/objects/companies/{company_id}",
            visible_fields=["company_id"],
        ),
        OpSpec(
            id="update_company",
            label="Update Company",
            method="PATCH",
            path="/crm/v3/objects/companies/{company_id}",
            visible_fields=["company_id", "company_name", "domain"],
            body_builder=lambda v: {
                "properties": {
                    k: val
                    for k, val in {
                        "name": getattr(v, "company_name", None) or None,
                        "domain": getattr(v, "domain", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="delete_company",
            label="Delete Company",
            method="DELETE",
            path="/crm/v3/objects/companies/{company_id}",
            visible_fields=["company_id"],
        ),
        OpSpec(
            id="search_companies",
            label="Search Companies",
            method="POST",
            path="/crm/v3/objects/companies/search",
            visible_fields=["query", "limit"],
            body_builder=lambda v: {
                "query": getattr(v, "query", None) or "",
                "limit": int(getattr(v, "limit", 20) or 20),
            },
        ),
        # ─── tickets ───────────────────────────────────────────────
        OpSpec(
            id="create_ticket",
            label="Create Ticket",
            method="POST",
            path="/crm/v3/objects/tickets",
            visible_fields=[
                "ticket_name",
                "ticket_pipeline",
                "ticket_stage",
                "ticket_content",
                "ticket_priority",
            ],
            body_builder=lambda v: {
                "properties": {
                    k: val
                    for k, val in {
                        "subject": getattr(v, "ticket_name", None) or None,
                        "hs_pipeline": getattr(v, "ticket_pipeline", None) or None,
                        "hs_pipeline_stage": getattr(v, "ticket_stage", None) or None,
                        "content": getattr(v, "ticket_content", None) or None,
                        "hs_ticket_priority": getattr(v, "ticket_priority", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="get_ticket",
            label="Get Ticket",
            method="GET",
            path="/crm/v3/objects/tickets/{ticket_id}",
            visible_fields=["ticket_id"],
        ),
        OpSpec(
            id="list_tickets",
            label="List Tickets",
            method="GET",
            path="/crm/v3/objects/tickets",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 20) or 20)},
        ),
        OpSpec(
            id="update_ticket",
            label="Update Ticket",
            method="PATCH",
            path="/crm/v3/objects/tickets/{ticket_id}",
            visible_fields=["ticket_id", "ticket_stage", "ticket_content"],
            body_builder=lambda v: {
                "properties": {
                    k: val
                    for k, val in {
                        "hs_pipeline_stage": getattr(v, "ticket_stage", None) or None,
                        "content": getattr(v, "ticket_content", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="delete_ticket",
            label="Delete Ticket",
            method="DELETE",
            path="/crm/v3/objects/tickets/{ticket_id}",
            visible_fields=["ticket_id"],
        ),
        # ─── engagements (notes/emails/tasks) ──────────────────────
        OpSpec(
            id="create_engagement",
            label="Create Engagement",
            method="POST",
            path="/engagements/v1/engagements",
            visible_fields=["engagement_type", "engagement_body", "contact_id"],
            body_builder=lambda v: {
                "engagement": {"type": (getattr(v, "engagement_type", None) or "NOTE").upper()},
                "associations": {"contactIds": [getattr(v, "contact_id", None)]}
                if getattr(v, "contact_id", None)
                else {},
                "metadata": {"body": getattr(v, "engagement_body", None) or ""},
            },
        ),
        OpSpec(
            id="get_engagement",
            label="Get Engagement",
            method="GET",
            path="/engagements/v1/engagements/{engagement_id}",
            visible_fields=["engagement_id"],
        ),
        OpSpec(
            id="delete_engagement",
            label="Delete Engagement",
            method="DELETE",
            path="/engagements/v1/engagements/{engagement_id}",
            visible_fields=["engagement_id"],
        ),
        # ─── associations ──────────────────────────────────────────
        OpSpec(
            id="associate",
            label="Associate Objects",
            method="PUT",
            path="/crm/v4/objects/{from_object_type}/{from_object_id}/associations/default/{to_object_type}/{to_object_id}",
            visible_fields=["from_object_id", "to_object_id"],
        ),
        # ─── lists ─────────────────────────────────────────────────
        OpSpec(
            id="list_lists",
            label="List Contact Lists",
            method="GET",
            path="/contacts/v1/lists",
            visible_fields=["limit"],
            query_builder=lambda v: {"count": int(getattr(v, "limit", 20) or 20)},
        ),
        OpSpec(
            id="get_list",
            label="Get Contact List",
            method="GET",
            path="/contacts/v1/lists/{list_id}",
            visible_fields=["list_id"],
        ),
        OpSpec(
            id="get_list_contacts",
            label="Get Contacts in List",
            method="GET",
            path="/contacts/v1/lists/{list_id}/contacts/all",
            visible_fields=["list_id"],
        ),
        # ─── owners + pipelines ────────────────────────────────────
        OpSpec(
            id="list_owners",
            label="List Owners",
            method="GET",
            path="/crm/v3/owners",
        ),
        OpSpec(
            id="get_owner",
            label="Get Owner",
            method="GET",
            path="/crm/v3/owners/{owner_id}",
            visible_fields=["owner_id"],
        ),
        OpSpec(
            id="list_deal_pipelines",
            label="List Deal Pipelines",
            method="GET",
            path="/crm/v3/pipelines/deals",
        ),
        OpSpec(
            id="list_ticket_pipelines",
            label="List Ticket Pipelines",
            method="GET",
            path="/crm/v3/pipelines/tickets",
        ),
        # ─── forms + email + files ─────────────────────────────────
        OpSpec(
            id="list_forms",
            label="List Forms",
            method="GET",
            path="/marketing/v3/forms",
        ),
        OpSpec(
            id="submit_form",
            label="Submit Form (public)",
            method="POST",
            path="/uploads/form/v2/{portal_id}/{form_guid}",
            visible_fields=["properties_body"],
            body_builder=lambda v: getattr(v, "properties_body", None) or {},
        ),
        # ─── property + object introspection ───────────────────────
        OpSpec(
            id="list_contact_properties",
            label="List Contact Properties",
            method="GET",
            path="/crm/v3/properties/contacts",
        ),
        OpSpec(
            id="list_deal_properties",
            label="List Deal Properties",
            method="GET",
            path="/crm/v3/properties/deals",
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
