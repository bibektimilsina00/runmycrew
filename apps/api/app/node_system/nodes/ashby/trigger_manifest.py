"""Ashby polling trigger — manifest form.

Ashby's list endpoints are POST-only, so we drop down to a custom
paginate_fn that POSTs with a `limit` body.

Events (4 poll-observable of sim's 6):
  - `candidate_new`             — known_ids on candidate.list
  - `offer_created`             — known_ids on offer.list
  - `application_stage_change`  — custom diff tracking
                                  {application_id: interview_stage_id}
  - `candidate_hired`           — since_timestamp on hiredAt

Not in polling (need webhooks):
  interview_completed, feedback_submitted — each requires
  per-application polling which is O(candidates) and impractical at
  scale. Ashby's native webhooks deliver these in real time.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    PollingEvent,
    PollingTriggerManifest,
    build_auth,
    register_flatten,
)

_ASHBY_API = "https://api.ashbyhq.com"


def _flatten_candidate(item):
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "email": item.get("primaryEmailAddress", {}).get("value")
        if isinstance(item.get("primaryEmailAddress"), dict)
        else item.get("email"),
        "phone": item.get("primaryPhoneNumber", {}).get("value")
        if isinstance(item.get("primaryPhoneNumber"), dict)
        else item.get("phoneNumber"),
        "company": item.get("company"),
        "title": item.get("position"),
        "location": item.get("locationSummary"),
        "linkedin_url": item.get("linkedInUrl"),
        "created_at": item.get("createdAt"),
        "updated_at": item.get("updatedAt"),
        "hired_at": item.get("hiredAt"),
    }


def _flatten_offer(item):
    return {
        "id": item.get("id"),
        "status": item.get("offerStatus"),
        "application_id": item.get("applicationId"),
        "job_id": item.get("jobId"),
        "created_at": item.get("createdAt"),
        "updated_at": item.get("updatedAt"),
    }


def _flatten_application(item):
    return {
        "id": item.get("id"),
        "candidate_id": item.get("candidateId"),
        "job_id": item.get("jobId"),
        "status": item.get("status"),
        "current_interview_stage": (item.get("currentInterviewStage") or {}).get("title"),
        "current_stage_id": (item.get("currentInterviewStage") or {}).get("id"),
        "applied_at": item.get("appliedAt"),
        "updated_at": item.get("updatedAt"),
    }


register_flatten("ashby.candidate", _flatten_candidate)
register_flatten("ashby.offer", _flatten_offer)
register_flatten("ashby.application", _flatten_application)


def _diff_stage_change(items, cursor, props, event_id):
    """Custom diff — fire when an application's current interview
    stage id changes. Cursor tracks `{application_id: stage_id}`; first
    poll snapshots silent (activation shouldn't flood the workflow with
    every existing application)."""
    prior = None
    if isinstance(cursor, dict) and cursor.get("event_type") == event_id:
        prior = cursor.get("stages") if isinstance(cursor.get("stages"), dict) else None

    new_stages: dict[str, str] = {}
    matches: list[dict[str, Any]] = []
    first_poll = prior is None
    for item in items:
        app_id = str(item.get("id") or "")
        if not app_id:
            continue
        stage_id = str((item.get("currentInterviewStage") or {}).get("id") or "")
        new_stages[app_id] = stage_id
        if first_poll:
            continue
        prev = prior.get(app_id) if isinstance(prior, dict) else None
        if prev is not None and prev != stage_id:
            flat = _flatten_application(item)
            flat["event_type"] = event_id
            flat["change"] = {"key": "stage", "from": prev, "to": stage_id}
            matches.append(flat)

    return matches, {"event_type": event_id, "stages": new_stages}


async def _walk_ashby(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """POST to the right list endpoint by event id."""
    auth_headers, _ = build_auth(
        token=token,
        scheme="basic_token_only",
        header_name="Authorization",
        value_template="",
        query_param="",
    )
    headers = {
        **auth_headers,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 200))
    except (TypeError, ValueError):
        limit = 25

    endpoint_by_event = {
        "candidate_new": "/candidate.list",
        "candidate_hired": "/candidate.list",
        "offer_created": "/offer.list",
        "application_stage_change": "/application.list",
    }
    path = endpoint_by_event.get(event.id)
    if not path:
        return []
    resp = await client.post(
        f"{_ASHBY_API}{path}",
        headers=headers,
        json={"limit": limit},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    if not payload.get("success", True) and payload.get("errors"):
        raise RuntimeError(str(payload["errors"])[:200])
    results = payload.get("results") or []
    if not isinstance(results, list):
        return []
    # Hoist hiredAt → updated for candidate_hired since_timestamp diff.
    if event.id == "candidate_hired":
        for c in results:
            if c.get("hiredAt"):
                c["updated"] = c["hiredAt"]
    return results


MANIFEST = PollingTriggerManifest(
    type="trigger.ashby",
    name="Ashby",
    description=("Poll Ashby ATS for new candidates, offers, application stage changes, or hires."),
    icon_slug="ashby",
    color="#1c1c1c",
    base_url=_ASHBY_API,
    credential_type="ashby_api_key",
    token_field=["api_key"],
    auth="basic_token_only",
    provider="ashby",
    default_poll_interval_seconds=90,
    common_fields=[],
    events=[
        PollingEvent(
            id="candidate_new",
            label="Candidate Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="ashby.candidate",
        ),
        PollingEvent(
            id="candidate_hired",
            label="Candidate Hired",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="ashby.candidate",
        ),
        PollingEvent(
            id="offer_created",
            label="Offer Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="ashby.offer",
        ),
        PollingEvent(
            id="application_stage_change",
            label="Application Stage Changed",
            list_path="",
            diff_handler=_diff_stage_change,
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "current_interview_stage", "type": "string"},
        {"label": "change", "type": "object"},
    ],
    paginate_fn=_walk_ashby,
)
