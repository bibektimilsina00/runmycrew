"""Unit tests for the ATS long-tail providers (Phase 4.6).

Covers the new `basic_token_only` auth scheme + the flatteners and
custom diff for greenhouse and ashby. Wire-level tests aren't
included — both providers need live keys.
"""

from __future__ import annotations

import base64

from apps.api.app.node_system.nodes.ashby.trigger_manifest import (
    _diff_stage_change,
)
from apps.api.app.node_system.nodes.ashby.trigger_manifest import (
    _flatten_application as ashby_flatten_application,
)
from apps.api.app.node_system.nodes.ashby.trigger_manifest import (
    _flatten_candidate as ashby_flatten_candidate,
)
from apps.api.app.node_system.nodes.ashby.trigger_manifest import (
    _flatten_offer as ashby_flatten_offer,
)
from apps.api.app.node_system.nodes.greenhouse.trigger_manifest import (
    _flatten_application as gh_flatten_application,
)
from apps.api.app.node_system.nodes.greenhouse.trigger_manifest import (
    _flatten_candidate as gh_flatten_candidate,
)
from apps.api.app.node_system.nodes.greenhouse.trigger_manifest import (
    _flatten_offer as gh_flatten_offer,
)
from apps.api.app.node_system.scaffolds.rest_dispatch import build_auth

# ── new auth scheme ──────────────────────────────────────────────────


def test_basic_token_only_encodes_key_with_empty_password() -> None:
    """Greenhouse expects `Basic base64(api_key:)`. Standard `basic`
    scheme would encode `username:token` — doubling the key. This test
    guards against a regression that puts anything after the colon."""
    headers, params = build_auth(
        token="ghs_xxx",
        scheme="basic_token_only",
        header_name="Authorization",
        value_template="",
        query_param="",
    )
    assert params == {}
    expected = "Basic " + base64.b64encode(b"ghs_xxx:").decode()
    assert headers["Authorization"] == expected


def test_basic_token_only_empty_token_returns_empty_header() -> None:
    """No token → no header. Prevents shipping `Basic Og==` (empty
    key, empty pw) which some APIs return 200 for."""
    headers, params = build_auth(
        token=None,
        scheme="basic_token_only",
        header_name="Authorization",
        value_template="",
        query_param="",
    )
    assert headers == {}
    assert params == {}


# ── greenhouse flatteners ────────────────────────────────────────────


def test_greenhouse_candidate_pulls_primary_email_and_phone() -> None:
    """Greenhouse ships email + phone as arrays; the flatten picks the
    first non-empty value so downstream nodes see a scalar."""
    c = {
        "id": 123,
        "first_name": "Alice",
        "last_name": "Chen",
        "email_addresses": [
            {"value": "", "type": "work"},  # empty — should be skipped
            {"value": "alice@x.io", "type": "personal"},
        ],
        "phone_numbers": [{"value": "+15551234", "type": "mobile"}],
        "created_at": "2026-07-01T09:00:00Z",
        "updated_at": "2026-07-04T12:00:00Z",
    }
    out = gh_flatten_candidate(c)
    assert out["email"] == "alice@x.io"
    assert out["phone"] == "+15551234"


def test_greenhouse_application_pulls_stage_and_job_ids() -> None:
    a = {
        "id": 456,
        "candidate_id": 123,
        "status": "active",
        "current_stage": {"name": "Onsite"},
        "jobs": [{"id": 111}, {"id": 222}],
        "applied_at": "2026-07-01T09:00:00Z",
        "last_activity_at": "2026-07-04T09:00:00Z",
    }
    out = gh_flatten_application(a)
    assert out["current_stage"] == "Onsite"
    assert out["job_ids"] == [111, 222]


def test_greenhouse_offer_hoists_status() -> None:
    out = gh_flatten_offer(
        {"id": 789, "status": "signed", "candidate_id": 123, "starts_at": "2026-08-01"}
    )
    assert out["status"] == "signed"
    assert out["candidate_id"] == 123


# ── ashby flatteners ────────────────────────────────────────────────


def test_ashby_candidate_hoists_primary_email_and_stage_id() -> None:
    """Ashby wraps email in `primaryEmailAddress.value`. Downstream
    nodes should see a scalar, not a nested envelope."""
    c = {
        "id": "cand_abc",
        "name": "Alice",
        "primaryEmailAddress": {"value": "alice@x.io"},
        "primaryPhoneNumber": {"value": "+15551234"},
        "position": "Engineer",
        "createdAt": "2026-07-01T09:00:00Z",
    }
    out = ashby_flatten_candidate(c)
    assert out["email"] == "alice@x.io"
    assert out["phone"] == "+15551234"
    assert out["title"] == "Engineer"


def test_ashby_application_pulls_stage_id() -> None:
    a = {
        "id": "app_xyz",
        "candidateId": "cand_abc",
        "jobId": "job_qrs",
        "status": "active",
        "currentInterviewStage": {"id": "stg_1", "title": "Onsite"},
        "appliedAt": "2026-07-01T09:00:00Z",
    }
    out = ashby_flatten_application(a)
    assert out["current_stage_id"] == "stg_1"
    assert out["current_interview_stage"] == "Onsite"


def test_ashby_offer_flatten() -> None:
    o = {"id": "off_1", "offerStatus": "extended", "applicationId": "app_xyz"}
    out = ashby_flatten_offer(o)
    assert out["status"] == "extended"


# ── ashby stage-change custom diff ──────────────────────────────────


class _Props:
    pass


def _app(app_id: str, stage_id: str) -> dict:
    return {
        "id": app_id,
        "candidateId": "cand_abc",
        "jobId": "job_qrs",
        "currentInterviewStage": {"id": stage_id, "title": f"Stage {stage_id}"},
    }


def test_ashby_stage_change_first_poll_snapshots_silent() -> None:
    apps = [_app("a1", "s1"), _app("a2", "s2")]
    matches, cursor = _diff_stage_change(apps, None, _Props(), "application_stage_change")
    assert matches == []
    assert cursor["stages"] == {"a1": "s1", "a2": "s2"}


def test_ashby_stage_change_fires_on_transition() -> None:
    prior = {"event_type": "application_stage_change", "stages": {"a1": "s1", "a2": "s2"}}
    apps = [_app("a1", "s2"), _app("a2", "s2")]  # a1 moved
    matches, cursor = _diff_stage_change(apps, prior, _Props(), "application_stage_change")
    assert len(matches) == 1
    assert matches[0]["id"] == "a1"
    assert matches[0]["change"] == {"key": "stage", "from": "s1", "to": "s2"}


# ── credential registration ─────────────────────────────────────────


def test_ats_credentials_registered() -> None:
    from apps.api.app.credential_manager.api_keys import PROVIDERS

    assert "greenhouse" in PROVIDERS
    assert "ashby" in PROVIDERS
    assert {f.id for f in PROVIDERS["greenhouse"].fields} == {"api_key"}
    assert {f.id for f in PROVIDERS["ashby"].fields} == {"api_key"}
