"""ZoomInfo action node — ZoomInfo — B2B contact + company database.

REST at https://api.zoominfo.com/lookup. See sim-parity roadmap Phase 4.16/4.17.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.zoominfo",
    name="ZoomInfo",
    category="integration",
    description="ZoomInfo — B2B contact + company database.",
    icon_slug="zoominfo",
    color="#1c1c1c",
    base_url="https://api.zoominfo.com/lookup",
    credential_type="zoominfo_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="linkedin_url", label="LinkedIn URL", type="string"),
        FieldSpec(name="domain", label="Domain / Website", type="string"),
        FieldSpec(name="company", label="Company Name", type="string"),
        FieldSpec(name="query", label="Search Query (JSON)", type="json", mode="advanced"),
        FieldSpec(name="size", label="Size", type="number", default=25, mode="advanced"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
        FieldSpec(name="per_page", label="Per Page", type="number", default=25, mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
        FieldSpec(name="inquiry_id", label="Inquiry ID", type="string"),
        FieldSpec(name="verification_id", label="Verification ID", type="string"),
        FieldSpec(name="account_id", label="Account ID", type="string"),
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="start_date", label="Start Date (YYYY-MM)", type="string"),
        FieldSpec(name="end_date", label="End Date (YYYY-MM)", type="string"),
    ],
    operations=[
        OpSpec(
            id="contact_enrich",
            label="Contact Enrichment",
            method="POST",
            path="/contact/enrich",
            visible_fields=["email", "first_name", "last_name", "company"],
            body_builder=lambda v: {
                "matchPersonInput": [
                    {
                        k: val
                        for k, val in {
                            "emailAddress": getattr(v, "email", None) or None,
                            "firstName": getattr(v, "first_name", None) or None,
                            "lastName": getattr(v, "last_name", None) or None,
                            "companyName": getattr(v, "company", None) or None,
                        }.items()
                        if val is not None
                    }
                ]
            },
        ),
        OpSpec(
            id="company_enrich",
            label="Company Enrichment",
            method="POST",
            path="/company/enrich",
            visible_fields=["domain", "company"],
            body_builder=lambda v: {
                "matchCompanyInput": [
                    {
                        k: val
                        for k, val in {
                            "companyWebsite": getattr(v, "domain", None) or None,
                            "companyName": getattr(v, "company", None) or None,
                        }.items()
                        if val is not None
                    }
                ]
            },
        ),
        OpSpec(
            id="contact_search",
            label="Contact Search",
            method="POST",
            path="/contact/search",
            visible_fields=["query", "size"],
            body_builder=lambda v: {
                **(getattr(v, "query", None) or {}),
                "rpp": int(getattr(v, "size", 25) or 25),
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "result", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
