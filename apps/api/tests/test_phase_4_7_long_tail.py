"""Unit tests for the Phase 4.7 long-tail providers (grain + lemlist)."""

from __future__ import annotations

from apps.api.app.node_system.nodes.grain.trigger_manifest import (
    _flatten_highlight,
    _flatten_recording,
    _flatten_story,
)
from apps.api.app.node_system.nodes.lemlist.trigger_manifest import (
    _flatten_activity,
    _flatten_lead,
)

# ── Grain ────────────────────────────────────────────────────────────


def test_grain_recording_pulls_owner_and_participants() -> None:
    """Owner + participants are nested arrays. The flatten hoists the
    first owner name and collapses participants to a plain list of
    name/email strings so downstream nodes can iterate cleanly."""
    r = {
        "id": "rec1",
        "title": "Weekly sync",
        "url": "https://grain.com/r/rec1",
        "start_datetime": "2026-07-04T10:00:00Z",
        "end_datetime": "2026-07-04T10:30:00Z",
        "created_datetime": "2026-07-04T10:31:00Z",
        "updated_datetime": "2026-07-04T10:35:00Z",
        "owners": [{"name": "Alice"}, {"name": "Bob"}],
        "participants": [
            {"name": "Alice", "email": "a@x.io"},
            {"email": "b@x.io"},  # no name — falls back to email
        ],
    }
    out = _flatten_recording(r)
    assert out["id"] == "rec1"
    assert out["owner_name"] == "Alice"
    assert out["participants"] == ["Alice", "b@x.io"]


def test_grain_recording_survives_empty_owners_and_participants() -> None:
    """Missing/empty arrays must not crash — Grain's API sometimes
    returns bare `null` for these fields on freshly-created rows."""
    r = {"id": "rec2", "owners": None, "participants": None}
    out = _flatten_recording(r)
    assert out["owner_name"] is None
    assert out["participants"] == []


def test_grain_highlight_pulls_creator_name_and_recording_ref() -> None:
    h = {
        "id": "h1",
        "text": "great point",
        "recording_id": "rec1",
        "timestamp": 300,
        "duration": 30,
        "created_by": {"name": "Alice"},
        "created_datetime": "2026-07-04T10:20:00Z",
    }
    out = _flatten_highlight(h)
    assert out["created_by_name"] == "Alice"
    assert out["recording_id"] == "rec1"
    assert out["duration"] == 30


def test_grain_story_counts_highlights() -> None:
    """Story flatten surfaces the highlight count so downstream
    condition nodes can gate on story length without walking the
    array themselves."""
    s = {
        "id": "s1",
        "title": "Q3 win",
        "highlights": [{"id": "h1"}, {"id": "h2"}, {"id": "h3"}],
    }
    out = _flatten_story(s)
    assert out["highlight_count"] == 3


# ── Lemlist ──────────────────────────────────────────────────────────


def test_lemlist_activity_carries_campaign_and_lead() -> None:
    """Activity events are the entry point for downstream email-event
    logic — flatten must surface campaign + lead identity."""
    a = {
        "_id": "act1",
        "type": "emailOpen",
        "campaignId": "camp1",
        "campaignName": "Q3 Outbound",
        "leadEmail": "prospect@x.io",
        "firstName": "Alice",
        "lastName": "Chen",
        "date": "2026-07-04T12:00:00Z",
    }
    out = _flatten_activity(a)
    assert out["id"] == "act1"
    assert out["type"] == "emailOpen"
    assert out["campaign_id"] == "camp1"
    assert out["lead_email"] == "prospect@x.io"


def test_lemlist_lead_hoists_added_at() -> None:
    lead = {
        "email": "p@x.io",
        "firstName": "Bob",
        "companyName": "Acme",
        "addedAt": "2026-07-01T09:00:00Z",
        "campaignId": "camp2",
    }
    out = _flatten_lead(lead)
    assert out["email"] == "p@x.io"
    assert out["added_at"] == "2026-07-01T09:00:00Z"
    assert out["campaign_id"] == "camp2"


# ── Credentials + Lemlist basic-auth shape ───────────────────────────


def test_long_tail_credentials_registered() -> None:
    from apps.api.app.credential_manager.api_keys import PROVIDERS

    assert "grain" in PROVIDERS
    assert "lemlist" in PROVIDERS
    assert {f.id for f in PROVIDERS["grain"].fields} == {"api_key"}
    assert {f.id for f in PROVIDERS["lemlist"].fields} == {"api_key"}


def test_lemlist_basic_auth_puts_key_as_password() -> None:
    """Lemlist's convention is `Basic base64(:api_key)` — empty
    username. Standard `basic` scheme with `basic_username=""` produces
    exactly that shape. Guard against a regression that puts the key
    in the username slot (like Greenhouse needs)."""
    import base64

    from apps.api.app.node_system.scaffolds.rest_dispatch import build_auth

    headers, _ = build_auth(
        token="lemlist_key",
        scheme="basic",
        header_name="Authorization",
        value_template="",
        query_param="",
        basic_username="",
    )
    expected = "Basic " + base64.b64encode(b":lemlist_key").decode()
    assert headers["Authorization"] == expected


def test_grain_trigger_events_match_sim_names() -> None:
    """Sim's grain events use recording_created / highlight_created /
    story_created — pull-observable subset. Our trigger names match so
    a migration from Sim doesn't rewrite event handlers."""
    from apps.api.app.node_system.nodes.grain.trigger_manifest import MANIFEST

    ids = {e.id for e in MANIFEST.events}
    assert {"recording_created", "highlight_created", "story_created"} <= ids
