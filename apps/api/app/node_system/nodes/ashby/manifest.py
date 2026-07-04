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
        FieldSpec(name="candidate_body", label="Candidate Body (JSON)", type="json", default={}),
        FieldSpec(name="candidate_query", label="Candidate Query", type="string"),
        FieldSpec(name="ashby_job_id", label="Job ID", type="string"),
        FieldSpec(name="note_content", label="Note Content", type="string"),
        FieldSpec(
            name="application_body", label="Application Body (JSON)", type="json", default={}
        ),
        FieldSpec(name="interview_stage_id", label="Interview Stage ID", type="string"),
        FieldSpec(name="tag_id", label="Tag ID", type="string"),
        FieldSpec(name="offer_id", label="Offer ID", type="string"),
        FieldSpec(name="job_posting_id", label="Job Posting ID", type="string"),
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
        OpSpec(
            id="search_candidates",
            label="Search Candidates",
            method="POST",
            path="/candidate.search",
            visible_fields=["candidate_query"],
            body_builder=lambda v: {"query": getattr(v, "candidate_query", None) or ""},
        ),
        OpSpec(
            id="create_note",
            label="Create Note on Candidate",
            method="POST",
            path="/candidate.createNote",
            visible_fields=["candidate_id", "note_content"],
            body_builder=lambda v: {
                "candidateId": getattr(v, "candidate_id", "") or "",
                "note": {"value": getattr(v, "note_content", "") or ""},
            },
        ),
        OpSpec(
            id="list_notes",
            label="List Notes on Candidate",
            method="POST",
            path="/candidate.listNotes",
            visible_fields=["candidate_id"],
            body_builder=lambda v: {"candidateId": getattr(v, "candidate_id", "") or ""},
        ),
        OpSpec(
            id="create_application",
            label="Create Application",
            method="POST",
            path="/application.create",
            visible_fields=["application_body"],
            body_builder=lambda v: getattr(v, "application_body", None) or {},
        ),
        OpSpec(
            id="list_offers",
            label="List Offers",
            method="POST",
            path="/offer.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="change_application_stage",
            label="Change Application Stage",
            method="POST",
            path="/application.change_stage",
            visible_fields=["application_id", "interview_stage_id"],
            body_builder=lambda v: {
                "applicationId": getattr(v, "application_id", "") or "",
                "interviewStageId": getattr(v, "interview_stage_id", "") or "",
            },
        ),
        OpSpec(
            id="add_candidate_tag",
            label="Add Tag to Candidate",
            method="POST",
            path="/candidate.addTag",
            visible_fields=["candidate_id", "tag_id"],
            body_builder=lambda v: {
                "candidateId": getattr(v, "candidate_id", "") or "",
                "tagId": getattr(v, "tag_id", "") or "",
            },
        ),
        OpSpec(
            id="remove_candidate_tag",
            label="Remove Tag from Candidate",
            method="POST",
            path="/candidate.removeTag",
            visible_fields=["candidate_id", "tag_id"],
            body_builder=lambda v: {
                "candidateId": getattr(v, "candidate_id", "") or "",
                "tagId": getattr(v, "tag_id", "") or "",
            },
        ),
        OpSpec(
            id="get_offer",
            label="Get Offer",
            method="POST",
            path="/offer.info",
            visible_fields=["offer_id"],
            body_builder=lambda v: {"offerId": getattr(v, "offer_id", "") or ""},
        ),
        OpSpec(
            id="list_sources",
            label="List Sources",
            method="POST",
            path="/source.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_candidate_tags",
            label="List Candidate Tags",
            method="POST",
            path="/candidateTag.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_archive_reasons",
            label="List Archive Reasons",
            method="POST",
            path="/archiveReason.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_custom_fields",
            label="List Custom Fields",
            method="POST",
            path="/customField.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_departments",
            label="List Departments",
            method="POST",
            path="/department.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_locations",
            label="List Locations",
            method="POST",
            path="/location.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_job_postings",
            label="List Job Postings",
            method="POST",
            path="/jobPosting.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="get_job_posting",
            label="Get Job Posting",
            method="POST",
            path="/jobPosting.info",
            visible_fields=["job_posting_id"],
            body_builder=lambda v: {"jobPostingId": getattr(v, "job_posting_id", "") or ""},
        ),
        OpSpec(
            id="list_openings",
            label="List Openings",
            method="POST",
            path="/opening.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_users",
            label="List Users",
            method="POST",
            path="/user.list",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_interviews",
            label="List Interviews",
            method="POST",
            path="/interview.list",
            visible_fields=[],
            body_builder=lambda v: {},
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
