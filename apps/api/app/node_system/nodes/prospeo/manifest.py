"""Prospeo action node — Prospeo — B2B email finder + verifier.

REST at https://api.prospeo.io. See sim-parity roadmap Phase 4.16/4.17.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.prospeo",
    name="Prospeo",
    category="integration",
    description="Prospeo — B2B email finder + verifier.",
    icon_slug="prospeo",
    color="#1c1c1c",
    base_url="https://api.prospeo.io",
    credential_type="prospeo_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-KEY",
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
            id="email_finder",
            label="Email Finder",
            method="POST",
            path="/email-finder",
            visible_fields=["first_name", "last_name", "domain"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                    "company": getattr(v, "domain", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="email_verifier",
            label="Email Verifier",
            method="POST",
            path="/email-verifier",
            visible_fields=["email"],
            body_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        OpSpec(
            id="linkedin_email_finder",
            label="LinkedIn Email Finder",
            method="POST",
            path="/linkedin-email-finder",
            visible_fields=["linkedin_url"],
            body_builder=lambda v: {"url": getattr(v, "linkedin_url", "") or ""},
        ),
        OpSpec(
            id="mobile_finder",
            label="Mobile Number Finder",
            method="POST",
            path="/mobile-finder",
            visible_fields=["linkedin_url"],
            body_builder=lambda v: {"url": getattr(v, "linkedin_url", "") or ""},
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
