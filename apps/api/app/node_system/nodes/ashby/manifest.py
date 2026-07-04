"""Ashby action node — manifest form.

Ashby uses POST-only JSON endpoints at `https://api.ashbyhq.com`
routed by URL like `candidate.list` / `candidate.create` /
`application.info` — an RPC-style flavor.

Auth: `Basic base64(api_key:)` — same shape as Greenhouse, uses the
scaffold's `basic_token_only` scheme.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.ashby",
    name="Ashby",
    category="integration",
    description="Ashby ATS — candidates, applications, jobs, feedback via POST RPC.",
    icon_slug="ashby",
    color="#1c1c1c",
    base_url="https://api.ashbyhq.com",
    credential_type="ashby_api_key",
    token_field=["api_key"],
    auth="basic_token_only",
    fields=[
        FieldSpec(name="candidate_id", label="Candidate ID", type="string"),
        FieldSpec(name="application_id", label="Application ID", type="string"),
        FieldSpec(name="job_id", label="Job ID", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="phone", label="Phone", type="string"),
        FieldSpec(name="company", label="Company", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="location", label="Location", type="string"),
        FieldSpec(name="linkedin_url", label="LinkedIn URL", type="string"),
        FieldSpec(
            name="cursor",
            label="Pagination Cursor",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="limit",
            label="Limit",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="list_candidates",
            label="List Candidates",
            method="POST",
            path="/candidate.list",
            visible_fields=["cursor", "limit"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "cursor": getattr(v, "cursor", None) or None,
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_candidate",
            label="Get Candidate Info",
            method="POST",
            path="/candidate.info",
            visible_fields=["candidate_id"],
            body_builder=lambda v: {"candidateId": getattr(v, "candidate_id", "") or ""},
        ),
        OpSpec(
            id="create_candidate",
            label="Create Candidate",
            method="POST",
            path="/candidate.create",
            visible_fields=[
                "first_name",
                "last_name",
                "email",
                "phone",
                "company",
                "title",
                "location",
                "linkedin_url",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "name": (
                        f"{getattr(v, 'first_name', '') or ''} {getattr(v, 'last_name', '') or ''}"
                    ).strip()
                    or None,
                    "email": getattr(v, "email", None) or None,
                    "phoneNumber": getattr(v, "phone", None) or None,
                    "company": getattr(v, "company", None) or None,
                    "title": getattr(v, "title", None) or None,
                    "location": getattr(v, "location", None) or None,
                    "linkedInUrl": getattr(v, "linkedin_url", None) or None,
                }.items()
                if val
            },
        ),
        OpSpec(
            id="update_candidate",
            label="Update Candidate",
            method="POST",
            path="/candidate.update",
            visible_fields=[
                "candidate_id",
                "first_name",
                "last_name",
                "email",
                "phone",
                "company",
                "title",
                "location",
                "linkedin_url",
            ],
            body_builder=lambda v: {
                "candidateId": getattr(v, "candidate_id", "") or "",
                **{
                    k: val
                    for k, val in {
                        "name": (
                            (
                                f"{getattr(v, 'first_name', '') or ''} "
                                f"{getattr(v, 'last_name', '') or ''}"
                            ).strip()
                            or None
                        ),
                        "email": getattr(v, "email", None) or None,
                        "phoneNumber": getattr(v, "phone", None) or None,
                        "company": getattr(v, "company", None) or None,
                        "title": getattr(v, "title", None) or None,
                        "location": getattr(v, "location", None) or None,
                        "linkedInUrl": getattr(v, "linkedin_url", None) or None,
                    }.items()
                    if val
                },
            },
        ),
        OpSpec(
            id="list_applications",
            label="List Applications",
            method="POST",
            path="/application.list",
            visible_fields=["cursor", "limit"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "cursor": getattr(v, "cursor", None) or None,
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_application",
            label="Get Application Info",
            method="POST",
            path="/application.info",
            visible_fields=["application_id"],
            body_builder=lambda v: {"applicationId": getattr(v, "application_id", "") or ""},
        ),
        OpSpec(
            id="list_jobs",
            label="List Jobs",
            method="POST",
            path="/job.list",
            visible_fields=["cursor", "limit"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "cursor": getattr(v, "cursor", None) or None,
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_job",
            label="Get Job Info",
            method="POST",
            path="/job.info",
            visible_fields=["job_id"],
            body_builder=lambda v: {"jobId": getattr(v, "job_id", "") or ""},
        ),
    ],
    outputs_schema=[
        {"label": "success", "type": "boolean"},
        {"label": "results", "type": "array"},
        {"label": "moreDataAvailable", "type": "boolean"},
        {"label": "nextCursor", "type": "string"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
