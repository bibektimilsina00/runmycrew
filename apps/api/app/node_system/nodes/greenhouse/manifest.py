"""Greenhouse action node — manifest form.

Harvest API v1 at `https://harvest.greenhouse.io/v1`. Auth is
`Basic base64(api_key:)` — token as username with empty password.
The scaffold's `basic_token_only` scheme handles that shape.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.greenhouse",
    name="Greenhouse",
    category="integration",
    description="Greenhouse ATS — jobs, candidates, applications, offers.",
    icon_slug="greenhouse",
    color="#1c1c1c",
    base_url="https://harvest.greenhouse.io/v1",
    credential_type="greenhouse_api_key",
    token_field=["api_key"],
    auth="basic_token_only",
    fields=[
        FieldSpec(name="job_id", label="Job ID", type="string"),
        FieldSpec(name="candidate_id", label="Candidate ID", type="string"),
        FieldSpec(name="application_id", label="Application ID", type="string"),
        FieldSpec(name="offer_id", label="Offer ID", type="string"),
        FieldSpec(
            name="user_id",
            label="User ID (for note authoring)",
            type="string",
            mode="advanced",
        ),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="phone", label="Phone", type="string"),
        FieldSpec(name="note_body", label="Note Body", type="string"),
        FieldSpec(
            name="visibility",
            label="Note Visibility",
            type="options",
            options=[
                {"label": "Admin only", "value": "admin_only"},
                {"label": "Public", "value": "public"},
                {"label": "Private", "value": "private"},
            ],
            default="admin_only",
            mode="advanced",
        ),
        FieldSpec(
            name="limit", label="Per page (max 500)", type="number", default=100, mode="advanced"
        ),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_jobs",
            label="List Jobs",
            method="GET",
            path="/jobs",
            visible_fields=["limit", "page"],
            query_builder=lambda v: {
                "per_page": int(getattr(v, "limit", 100) or 100),
                "page": int(getattr(v, "page", 1) or 1),
            },
        ),
        OpSpec(
            id="get_job",
            label="Get Job",
            method="GET",
            path="/jobs/{job_id}",
            visible_fields=["job_id"],
        ),
        OpSpec(
            id="list_candidates",
            label="List Candidates",
            method="GET",
            path="/candidates",
            visible_fields=["limit", "page"],
            query_builder=lambda v: {
                "per_page": int(getattr(v, "limit", 100) or 100),
                "page": int(getattr(v, "page", 1) or 1),
            },
        ),
        OpSpec(
            id="get_candidate",
            label="Get Candidate",
            method="GET",
            path="/candidates/{candidate_id}",
            visible_fields=["candidate_id"],
        ),
        OpSpec(
            id="create_candidate",
            label="Create Candidate",
            method="POST",
            path="/candidates",
            visible_fields=["first_name", "last_name", "email", "phone"],
            body_builder=lambda v: {
                "first_name": getattr(v, "first_name", None) or "",
                "last_name": getattr(v, "last_name", None) or "",
                **(
                    {"email_addresses": [{"value": v.email, "type": "personal"}]}
                    if getattr(v, "email", None)
                    else {}
                ),
                **(
                    {"phone_numbers": [{"value": v.phone, "type": "mobile"}]}
                    if getattr(v, "phone", None)
                    else {}
                ),
            },
        ),
        OpSpec(
            id="list_applications",
            label="List Applications",
            method="GET",
            path="/applications",
            visible_fields=["candidate_id", "job_id", "limit", "page"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "candidate_id": getattr(v, "candidate_id", None) or None,
                    "job_id": getattr(v, "job_id", None) or None,
                    "per_page": int(getattr(v, "limit", 100) or 100),
                    "page": int(getattr(v, "page", 1) or 1),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_application",
            label="Get Application",
            method="GET",
            path="/applications/{application_id}",
            visible_fields=["application_id"],
        ),
        OpSpec(
            id="add_candidate_note",
            label="Add Note to Candidate",
            method="POST",
            path="/candidates/{candidate_id}/activity_feed/notes",
            visible_fields=["candidate_id", "note_body", "visibility", "user_id"],
            body_builder=lambda v: {
                "user_id": int(getattr(v, "user_id", 0) or 0) or None,
                "body": getattr(v, "note_body", None) or "",
                "visibility": getattr(v, "visibility", None) or "admin_only",
            },
        ),
        OpSpec(
            id="list_offers",
            label="List Offers",
            method="GET",
            path="/offers",
            visible_fields=["limit", "page"],
            query_builder=lambda v: {
                "per_page": int(getattr(v, "limit", 100) or 100),
                "page": int(getattr(v, "page", 1) or 1),
            },
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "number"},
        {"label": "name", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "candidate", "type": "object"},
        {"label": "job", "type": "object"},
        {"label": "results", "type": "array"},
    ],
    allow_error=True,
)
