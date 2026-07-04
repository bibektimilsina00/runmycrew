"""Unit tests for Phase 4.12 vercel + typeform webhook triggers."""

from __future__ import annotations

from apps.api.app.node_system.nodes.typeform import (
    typeform_webhook as _tf_wh,  # noqa: F401
)
from apps.api.app.node_system.nodes.typeform.webhook_manifest import (
    MANIFEST as TYPEFORM,
)
from apps.api.app.node_system.nodes.typeform.webhook_manifest import (
    _flatten_answer,
)
from apps.api.app.node_system.nodes.typeform.webhook_manifest import (
    _shape as typeform_shape,
)
from apps.api.app.node_system.nodes.vercel import (
    vercel_webhook as _v_wh,  # noqa: F401
)
from apps.api.app.node_system.nodes.vercel.webhook_manifest import (
    MANIFEST as VERCEL,
)
from apps.api.app.node_system.nodes.vercel.webhook_manifest import (
    _shape as vercel_shape,
)

# ── Vercel ───────────────────────────────────────────────────────────


def test_vercel_shape_hoists_deployment_context() -> None:
    body = {
        "type": "deployment.succeeded",
        "id": "evt1",
        "team": {"id": "team1"},
        "user": {"id": "u1"},
        "payload": {
            "target": "production",
            "deployment": {
                "id": "dpl_abc",
                "url": "my-app-abc.vercel.app",
                "meta": {
                    "githubCommitSha": "deadbeef",
                    "githubCommitMessage": "fix: bug",
                },
            },
            "project": {"id": "prj1", "name": "my-app"},
            "region": "iad1",
        },
    }
    out = vercel_shape(body, "deployment.succeeded", "d1")
    assert out["event"] == "deployment.succeeded"
    assert out["deployment_id"] == "dpl_abc"
    assert out["deployment_url"] == "my-app-abc.vercel.app"
    assert out["deployment_state"] == "production"
    assert out["project_name"] == "my-app"
    assert out["commit_sha"] == "deadbeef"
    assert out["commit_message"] == "fix: bug"


def test_vercel_shape_survives_missing_payload_envelope() -> None:
    """Minimal delivery shouldn't crash — Vercel can send project.created
    with just a project reference and no deployment context."""
    body = {"type": "project.created", "payload": {"project": "prj_x"}}
    out = vercel_shape(body, "project.created", "d2")
    assert out["event"] == "project.created"
    assert out["project_id"] == "prj_x"


def test_vercel_full_sim_parity() -> None:
    values = {e.value for e in VERCEL.events}
    expected = {
        "deployment.created",
        "deployment.succeeded",
        "deployment.ready",
        "deployment.canceled",
        "deployment.error",
        "deployment.promoted",
        "project.created",
    }
    assert expected == values


def test_vercel_uses_sha1_scheme() -> None:
    """Vercel signs with SHA1, not SHA256 — regression guard against a
    copy-paste that swapped the algorithm."""
    assert VERCEL.signature.scheme == "hmac_sha1"
    assert VERCEL.signature.header_name == "x-vercel-signature"
    assert VERCEL.signature.prefix == ""


# ── Typeform ─────────────────────────────────────────────────────────


def test_typeform_flatten_answer_covers_all_common_types() -> None:
    """Typeform ships each answer type-specifically. The flatten
    hoists `value` regardless of type so downstream nodes read the
    same key."""
    text_answer = _flatten_answer(
        {"type": "text", "text": "hello", "field": {"id": "f1", "ref": "name"}}
    )
    assert text_answer["value"] == "hello"

    email_answer = _flatten_answer(
        {"type": "email", "email": "p@x.io", "field": {"id": "f2", "ref": "email"}}
    )
    assert email_answer["value"] == "p@x.io"

    number_answer = _flatten_answer(
        {"type": "number", "number": 42, "field": {"id": "f3", "ref": "age"}}
    )
    assert number_answer["value"] == 42

    choice_answer = _flatten_answer(
        {
            "type": "choice",
            "choice": {"label": "Yes"},
            "field": {"id": "f4", "ref": "consent"},
        }
    )
    assert choice_answer["value"] == "Yes"

    choices_answer = _flatten_answer(
        {
            "type": "choices",
            "choices": {"labels": ["red", "blue"]},
            "field": {"id": "f5", "ref": "colors"},
        }
    )
    assert choices_answer["value"] == ["red", "blue"]

    bool_answer = _flatten_answer(
        {"type": "boolean", "boolean": True, "field": {"id": "f6", "ref": "agreed"}}
    )
    assert bool_answer["value"] is True


def test_typeform_shape_builds_by_ref_map() -> None:
    """`by_ref` is the killer feature — user picks a stable `ref` per
    field in Typeform, workflow reads `answers.<ref>` without walking
    the array. Guard the mapping stays flat."""
    body = {
        "event_id": "evt_x",
        "event_type": "form_response",
        "form_response": {
            "response_id": "r1",
            "submitted_at": "2026-07-04T12:00:00Z",
            "definition": {"id": "form1", "title": "Signup"},
            "hidden": {"utm_source": "twitter"},
            "answers": [
                {
                    "type": "text",
                    "text": "Alice",
                    "field": {"id": "f1", "ref": "name", "title": "Name"},
                },
                {
                    "type": "email",
                    "email": "a@x.io",
                    "field": {"id": "f2", "ref": "email", "title": "Email"},
                },
            ],
        },
    }
    out = typeform_shape(body, "form_response", "evt_x")
    assert out["form_id"] == "form1"
    assert out["response_id"] == "r1"
    assert out["hidden"] == {"utm_source": "twitter"}
    assert out["by_ref"] == {"name": "Alice", "email": "a@x.io"}


def test_typeform_shape_skips_refs_without_ref_field() -> None:
    """Answers whose field has no `ref` don't appear in by_ref — that
    key set stays stable across form edits."""
    body = {
        "event_type": "form_response",
        "form_response": {
            "answers": [
                {"type": "text", "text": "hi", "field": {"id": "f1"}},  # no ref
                {
                    "type": "text",
                    "text": "with-ref",
                    "field": {"id": "f2", "ref": "greeting"},
                },
            ]
        },
    }
    out = typeform_shape(body, "form_response", "d")
    assert out["by_ref"] == {"greeting": "with-ref"}


def test_typeform_uses_hmac_sha256_b64_scheme() -> None:
    """Typeform signs with base64-encoded HMAC-SHA256 (sha256= prefix).
    Regression guard: standard hmac_sha256 (hex) wouldn't verify."""
    assert TYPEFORM.signature.scheme == "hmac_sha256_b64"
    assert TYPEFORM.signature.header_name == "Typeform-Signature"
    assert TYPEFORM.signature.prefix == "sha256="
