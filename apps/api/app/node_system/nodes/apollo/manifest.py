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
    color="#1c1c1c",
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
    ],
    outputs_schema=[
        {"label": "people", "type": "array"},
        {"label": "organizations", "type": "array"},
        {"label": "person", "type": "object"},
        {"label": "organization", "type": "object"},
    ],
    allow_error=True,
)
