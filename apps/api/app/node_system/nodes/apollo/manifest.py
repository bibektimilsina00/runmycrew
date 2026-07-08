"""Apollo.io action node — B2B contact search + email finder.

REST API at https://api.apollo.io/v1. Auth via X-Api-Key header
(header_token scheme).
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.apollo",
    name="Apollo.io",
    category="integration",
    description="Apollo — B2B contact search, email finder, sequences.",
    icon_slug="apollo",
    color="#ffffff",
    base_url="https://api.apollo.io/v1",
    credential_type="apollo_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-Api-Key",
    fields=[
        FieldSpec(name="q_organization_domains", label="Company Domain", type="string"),
        FieldSpec(name="person_titles", label="Titles (comma-separated)", type="string"),
        FieldSpec(name="q_keywords", label="Keywords", type="string"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
        FieldSpec(name="per_page", label="Per Page", type="number", default=10, mode="advanced"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="domain", label="Domain (for org enrich)", type="string"),
        FieldSpec(name="sequence_id", label="Sequence ID", type="string"),
        FieldSpec(name="contact_id", label="Contact ID", type="string"),
        FieldSpec(name="search_body", label="Search Body (JSON)", type="json", default={}),
        FieldSpec(name="bulk_details", label="Bulk Details (JSON array)", type="json", default=[]),
        FieldSpec(name="contact_body", label="Contact Body (JSON)", type="json", default={}),
        FieldSpec(name="account_id", label="Account ID", type="string"),
        FieldSpec(name="account_body", label="Account Body (JSON)", type="json", default={}),
        FieldSpec(name="opportunity_id", label="Opportunity ID", type="string"),
        FieldSpec(
            name="opportunity_body", label="Opportunity Body (JSON)", type="json", default={}
        ),
        FieldSpec(name="contact_ids", label="Contact IDs (JSON array)", type="json", default=[]),
        FieldSpec(name="task_body", label="Task Body (JSON)", type="json", default={}),
    ],
    operations=[
        OpSpec(
            id="search_people",
            label="Search People",
            method="POST",
            path="/mixed_people/search",
            visible_fields=[
                "q_organization_domains",
                "person_titles",
                "q_keywords",
                "page",
                "per_page",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "q_organization_domains": getattr(v, "q_organization_domains", None) or None,
                    "person_titles": [
                        t.strip()
                        for t in (getattr(v, "person_titles", "") or "").split(",")
                        if t.strip()
                    ]
                    or None,
                    "q_keywords": getattr(v, "q_keywords", None) or None,
                    "page": int(getattr(v, "page", 1) or 1),
                    "per_page": int(getattr(v, "per_page", 10) or 10),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="search_organizations",
            label="Search Organizations",
            method="POST",
            path="/mixed_companies/search",
            visible_fields=["q_organization_domains", "q_keywords", "page", "per_page"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "q_organization_domains": getattr(v, "q_organization_domains", None) or None,
                    "q_keywords": getattr(v, "q_keywords", None) or None,
                    "page": int(getattr(v, "page", 1) or 1),
                    "per_page": int(getattr(v, "per_page", 10) or 10),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="match_person",
            label="Match / Enrich Person",
            method="POST",
            path="/people/match",
            visible_fields=["first_name", "last_name", "email", "domain"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                    "email": getattr(v, "email", None) or None,
                    "domain": getattr(v, "domain", None) or None,
                    "reveal_personal_emails": True,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="enrich_organization",
            label="Enrich Organization",
            method="GET",
            path="/organizations/enrich",
            visible_fields=["domain"],
            query_builder=lambda v: {"domain": getattr(v, "domain", "") or ""},
        ),
        OpSpec(
            id="add_contact_to_sequence",
            label="Add Contact to Sequence",
            method="POST",
            path="/emailer_campaigns/{sequence_id}/add_contact_ids",
            visible_fields=["sequence_id", "contact_id"],
            body_builder=lambda v: {"contact_ids": [getattr(v, "contact_id", "") or ""]},
        ),
        OpSpec(
            id="people_search",
            label="People Search",
            method="POST",
            path="/api/v1/mixed_people/search",
            visible_fields=["search_body"],
            body_builder=lambda v: getattr(v, "search_body", None) or {},
        ),
        OpSpec(
            id="people_enrich",
            label="People Enrich",
            method="POST",
            path="/api/v1/people/match",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        OpSpec(
            id="people_bulk_enrich",
            label="People Bulk Enrich",
            method="POST",
            path="/api/v1/people/bulk_match",
            visible_fields=["bulk_details"],
            body_builder=lambda v: {"details": getattr(v, "bulk_details", []) or []},
        ),
        OpSpec(
            id="organization_search",
            label="Organization Search",
            method="POST",
            path="/api/v1/mixed_companies/search",
            visible_fields=["search_body"],
            body_builder=lambda v: getattr(v, "search_body", None) or {},
        ),
        OpSpec(
            id="organization_enrich",
            label="Organization Enrich",
            method="GET",
            path="/api/v1/organizations/enrich",
            visible_fields=["domain"],
            query_builder=lambda v: {"domain": getattr(v, "domain", "") or ""},
        ),
        OpSpec(
            id="organization_bulk_enrich",
            label="Organization Bulk Enrich",
            method="POST",
            path="/api/v1/organizations/bulk_enrich",
            visible_fields=["bulk_details"],
            body_builder=lambda v: {"details": getattr(v, "bulk_details", []) or []},
        ),
        OpSpec(
            id="contact_create",
            label="Create Contact",
            method="POST",
            path="/api/v1/contacts",
            visible_fields=["contact_body"],
            body_builder=lambda v: getattr(v, "contact_body", None) or {},
        ),
        OpSpec(
            id="contact_update",
            label="Update Contact",
            method="PUT",
            path="/api/v1/contacts/{contact_id}",
            visible_fields=["contact_id", "contact_body"],
            body_builder=lambda v: getattr(v, "contact_body", None) or {},
        ),
        OpSpec(
            id="contact_search",
            label="Search Contacts",
            method="POST",
            path="/api/v1/contacts/search",
            visible_fields=["search_body"],
            body_builder=lambda v: getattr(v, "search_body", None) or {},
        ),
        OpSpec(
            id="contact_bulk_create",
            label="Bulk Create Contacts",
            method="POST",
            path="/api/v1/contacts/bulk_create",
            visible_fields=["bulk_details"],
            body_builder=lambda v: {"contacts": getattr(v, "bulk_details", []) or []},
        ),
        OpSpec(
            id="contact_bulk_update",
            label="Bulk Update Contacts",
            method="POST",
            path="/api/v1/contacts/bulk_update",
            visible_fields=["bulk_details"],
            body_builder=lambda v: {"contacts": getattr(v, "bulk_details", []) or []},
        ),
        OpSpec(
            id="account_create",
            label="Create Account",
            method="POST",
            path="/api/v1/accounts",
            visible_fields=["account_body"],
            body_builder=lambda v: getattr(v, "account_body", None) or {},
        ),
        OpSpec(
            id="account_update",
            label="Update Account",
            method="PUT",
            path="/api/v1/accounts/{account_id}",
            visible_fields=["account_id", "account_body"],
            body_builder=lambda v: getattr(v, "account_body", None) or {},
        ),
        OpSpec(
            id="account_search",
            label="Search Accounts",
            method="POST",
            path="/api/v1/accounts/search",
            visible_fields=["search_body"],
            body_builder=lambda v: getattr(v, "search_body", None) or {},
        ),
        OpSpec(
            id="account_bulk_create",
            label="Bulk Create Accounts",
            method="POST",
            path="/api/v1/accounts/bulk_create",
            visible_fields=["bulk_details"],
            body_builder=lambda v: {"accounts": getattr(v, "bulk_details", []) or []},
        ),
        OpSpec(
            id="opportunity_create",
            label="Create Opportunity",
            method="POST",
            path="/api/v1/opportunities",
            visible_fields=["opportunity_body"],
            body_builder=lambda v: getattr(v, "opportunity_body", None) or {},
        ),
        OpSpec(
            id="opportunity_search",
            label="Search Opportunities",
            method="POST",
            path="/api/v1/opportunities/search",
            visible_fields=["search_body"],
            body_builder=lambda v: getattr(v, "search_body", None) or {},
        ),
        OpSpec(
            id="opportunity_get",
            label="Get Opportunity",
            method="GET",
            path="/api/v1/opportunities/{opportunity_id}",
            visible_fields=["opportunity_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="opportunity_update",
            label="Update Opportunity",
            method="PUT",
            path="/api/v1/opportunities/{opportunity_id}",
            visible_fields=["opportunity_id", "opportunity_body"],
            body_builder=lambda v: getattr(v, "opportunity_body", None) or {},
        ),
        OpSpec(
            id="sequence_search",
            label="Search Sequences",
            method="POST",
            path="/api/v1/sequences/search",
            visible_fields=["search_body"],
            body_builder=lambda v: getattr(v, "search_body", None) or {},
        ),
        OpSpec(
            id="sequence_add",
            label="Add Contact to Sequence",
            method="POST",
            path="/api/v1/sequences/{sequence_id}/add_contact_ids",
            visible_fields=["sequence_id", "contact_ids"],
            body_builder=lambda v: {"contact_ids": getattr(v, "contact_ids", []) or []},
        ),
        OpSpec(
            id="task_create",
            label="Create Task",
            method="POST",
            path="/api/v1/tasks",
            visible_fields=["task_body"],
            body_builder=lambda v: getattr(v, "task_body", None) or {},
        ),
        OpSpec(
            id="task_search",
            label="Search Tasks",
            method="POST",
            path="/api/v1/tasks/search",
            visible_fields=["search_body"],
            body_builder=lambda v: getattr(v, "search_body", None) or {},
        ),
        OpSpec(
            id="email_accounts",
            label="List Email Accounts",
            method="GET",
            path="/api/v1/email_accounts",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "people", "type": "array"},
        {"label": "organizations", "type": "array"},
        {"label": "person", "type": "object"},
        {"label": "organization", "type": "object"},
    ],
    allow_error=True,
)
