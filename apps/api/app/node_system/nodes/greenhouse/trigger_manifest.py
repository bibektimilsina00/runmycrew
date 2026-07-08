"""Greenhouse polling trigger — manifest form.

Harvest API v1 with `basic_token_only` auth (api_key as username,
empty password — same shape as the action node).

Events (5 poll-observable; sim ships 6 including offer_created):
  - `candidate_created`  — known_ids on candidates
  - `candidate_updated`  — since_timestamp on updated_at
  - `application_created`- known_ids on applications
  - `application_updated`- since_timestamp on last_activity_at
  - `job_created`        — known_ids on jobs
  - `offer_created`      — known_ids on offers

Not in polling — need webhook: prospect_created (Greenhouse's
"prospect" state transition isn't queryable via list endpoints).
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.greenhouse import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_candidate(item):
    return {
        "id": item.get("id"),
        "first_name": item.get("first_name"),
        "last_name": item.get("last_name"),
        "email": next(
            (
                e.get("value")
                for e in (item.get("email_addresses") or [])
                if isinstance(e, dict) and e.get("value")
            ),
            None,
        ),
        "phone": next(
            (
                p.get("value")
                for p in (item.get("phone_numbers") or [])
                if isinstance(p, dict) and p.get("value")
            ),
            None,
        ),
        "company": item.get("company"),
        "title": item.get("title"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "url": item.get("url"),
    }


def _flatten_application(item):
    return {
        "id": item.get("id"),
        "candidate_id": item.get("candidate_id"),
        "status": item.get("status"),
        "current_stage": (item.get("current_stage") or {}).get("name"),
        "job_ids": [j.get("id") for j in (item.get("jobs") or []) if isinstance(j, dict)],
        "applied_at": item.get("applied_at"),
        "last_activity_at": item.get("last_activity_at"),
        "rejected_at": item.get("rejected_at"),
        "source_name": (item.get("source") or {}).get("public_name"),
    }


def _flatten_job(item):
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "status": item.get("status"),
        "confidential": item.get("confidential"),
        "notes": item.get("notes"),
        "opened_at": item.get("opened_at"),
        "closed_at": item.get("closed_at"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "departments": [
            d.get("name") for d in (item.get("departments") or []) if isinstance(d, dict)
        ],
        "offices": [o.get("name") for o in (item.get("offices") or []) if isinstance(o, dict)],
    }


def _flatten_offer(item):
    return {
        "id": item.get("id"),
        "status": item.get("status"),
        "candidate_id": item.get("candidate_id"),
        "application_id": item.get("application_id"),
        "created_at": item.get("created_at"),
        "sent_at": item.get("sent_at"),
        "resolved_at": item.get("resolved_at"),
        "starts_at": item.get("starts_at"),
    }


register_flatten("greenhouse.candidate", _flatten_candidate)
register_flatten("greenhouse.application", _flatten_application)
register_flatten("greenhouse.job", _flatten_job)
register_flatten("greenhouse.offer", _flatten_offer)


MANIFEST = PollingTriggerManifest(
    type="trigger.greenhouse",
    name=NAME,
    description=(
        "Poll Greenhouse ATS for new / updated candidates, applications, jobs, or offers."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://harvest.greenhouse.io/v1",
    credential_type="greenhouse_api_key",
    token_field=["api_key"],
    auth="basic_token_only",
    provider="greenhouse",
    default_poll_interval_seconds=90,
    common_fields=[
        FieldSpec(
            name="per_page",
            label="Per page (max 500)",
            type="number",
            default=100,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="candidate_created",
            label="Candidate Created",
            list_path="/candidates",
            list_params={"per_page": "{per_page}"},
            strategy="known_ids",
            id_field="id",
            flatten="greenhouse.candidate",
        ),
        PollingEvent(
            id="candidate_updated",
            label="Candidate Updated",
            list_path="/candidates",
            list_params={"per_page": "{per_page}"},
            strategy="since_timestamp",
            timestamp_field="updated_at",
            flatten="greenhouse.candidate",
        ),
        PollingEvent(
            id="application_created",
            label="Application Created",
            list_path="/applications",
            list_params={"per_page": "{per_page}"},
            strategy="known_ids",
            id_field="id",
            flatten="greenhouse.application",
        ),
        PollingEvent(
            id="application_updated",
            label="Application Updated",
            list_path="/applications",
            list_params={"per_page": "{per_page}"},
            strategy="since_timestamp",
            timestamp_field="last_activity_at",
            flatten="greenhouse.application",
        ),
        PollingEvent(
            id="job_created",
            label="Job Created",
            list_path="/jobs",
            list_params={"per_page": "{per_page}"},
            strategy="known_ids",
            id_field="id",
            flatten="greenhouse.job",
        ),
        PollingEvent(
            id="offer_created",
            label="Offer Created",
            list_path="/offers",
            list_params={"per_page": "{per_page}"},
            strategy="known_ids",
            id_field="id",
            flatten="greenhouse.offer",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "number"},
        {"label": "first_name", "type": "string"},
        {"label": "last_name", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "created_at", "type": "string"},
        {"label": "updated_at", "type": "string"},
    ],
)
