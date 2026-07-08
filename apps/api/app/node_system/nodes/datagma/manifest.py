"""Datagma action node — Datagma — French B2B contact + company enrichment.

REST at https://gateway.datagma.net/api/ingress/v6. See sim-parity roadmap §4.15.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.datagma",
    name="Datagma",
    category="integration",
    description="Datagma — French B2B contact + company enrichment.",
    icon_slug="datagma",
    color="#ffffff",
    base_url="https://gateway.datagma.net/api/ingress/v6",
    credential_type="datagma_api_key",
    token_field=["api_key"],
    auth="query_token",
    auth_query_param="apiId",
    fields=[
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="linkedin_url", label="LinkedIn URL", type="string"),
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="company", label="Company Name", type="string"),
    ],
    operations=[
        OpSpec(
            id="full_person",
            label="Full Person Lookup",
            method="GET",
            path="/full",
            visible_fields=["email", "first_name", "last_name", "domain"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None) or None,
                    "firstName": getattr(v, "first_name", None) or None,
                    "lastName": getattr(v, "last_name", None) or None,
                    "domain": getattr(v, "domain", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="company",
            label="Company Lookup",
            method="GET",
            path="/business",
            visible_fields=["domain"],
            query_builder=lambda v: {"domain": getattr(v, "domain", "") or ""},
        ),
        OpSpec(
            id="find_email",
            label="Find Email",
            method="GET",
            path="/findEmail",
            visible_fields=["first_name", "last_name", "domain"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "firstName": getattr(v, "first_name", None) or None,
                    "lastName": getattr(v, "last_name", None) or None,
                    "domain": getattr(v, "domain", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="phone_search",
            label="Phone Search",
            method="GET",
            path="/phone",
            visible_fields=["first_name", "last_name", "company"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "firstName": getattr(v, "first_name", None) or None,
                    "lastName": getattr(v, "last_name", None) or None,
                    "company": getattr(v, "company", None) or None,
                }.items()
                if val is not None
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
