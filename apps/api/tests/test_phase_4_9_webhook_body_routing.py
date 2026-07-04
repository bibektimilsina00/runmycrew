"""Unit tests for Phase 4.9 outbound webhooks + body-based event routing.

Instantly / Lemlist / Emailbison don't ship an event header — the
event kind lives in the JSON body. Extends the scaffold with
`event_body_path` and dotted-path extraction. Test coverage:
  - the path helper handles hits, misses, nested keys, non-dict roots
  - the manifests wire event_body_path correctly
  - end-to-end payload_shape for each provider projects the right
    fields (campaign / lead / message / event)
"""

from __future__ import annotations

from apps.api.app.features.webhooks.service import _extract_body_path
from apps.api.app.node_system.nodes.emailbison.webhook_manifest import (
    MANIFEST as EMAILBISON,
)
from apps.api.app.node_system.nodes.emailbison.webhook_manifest import (
    _shape as emailbison_shape,
)
from apps.api.app.node_system.nodes.instantly.webhook_manifest import (
    MANIFEST as INSTANTLY,
)
from apps.api.app.node_system.nodes.instantly.webhook_manifest import (
    _shape as instantly_shape,
)
from apps.api.app.node_system.nodes.lemlist.webhook_manifest import (
    MANIFEST as LEMLIST,
)
from apps.api.app.node_system.nodes.lemlist.webhook_manifest import (
    _shape as lemlist_shape,
)

# ── dotted-path extraction ──────────────────────────────────────────


def test_extract_body_path_walks_dotted_keys() -> None:
    assert _extract_body_path({"event_type": "reply_received"}, "event_type") == "reply_received"
    assert _extract_body_path({"meta": {"event": "click"}}, "meta.event") == "click"


def test_extract_body_path_returns_empty_on_miss() -> None:
    assert _extract_body_path({}, "event_type") == ""
    assert _extract_body_path({"a": {"b": None}}, "a.b") == ""
    assert _extract_body_path({"a": 1}, "a.b.c") == ""  # a is not a dict


def test_extract_body_path_refuses_container_values() -> None:
    """Path should resolve to a scalar. If it lands on a dict/list,
    return empty — the receiver expects a stringy event type, not a
    structure it would try to compare against the filter dropdown."""
    assert _extract_body_path({"event": ["x"]}, "event") == ""
    assert _extract_body_path({"event": {"nested": "x"}}, "event") == ""


# ── manifests wire the path correctly ───────────────────────────────


def test_manifests_declare_event_body_path() -> None:
    assert INSTANTLY.event_body_path == "event_type"
    assert LEMLIST.event_body_path == "type"
    assert EMAILBISON.event_body_path == "event"


def test_manifests_cover_sim_event_range() -> None:
    """Sanity check on event counts — sim has 20 instantly, 8 lemlist,
    17 emailbison; we don't need parity but we should surface most of
    the customer-facing ones."""
    assert len(INSTANTLY.events) >= 15
    assert len(LEMLIST.events) >= 6
    assert len(EMAILBISON.events) >= 8


# ── payload_shape smoke ─────────────────────────────────────────────


def test_instantly_shape_pulls_lead_and_campaign_context() -> None:
    body = {
        "event_type": "reply_received",
        "workspace": "ws1",
        "data": {
            "campaign_id": "camp1",
            "lead_id": "lead1",
            "email": "prospect@x.io",
            "message_id": "msg1",
            "reply_content": "Sounds good",
        },
    }
    out = instantly_shape(body, "reply_received", "d1")
    assert out["event"] == "reply_received"
    assert out["campaign_id"] == "camp1"
    assert out["lead_email"] == "prospect@x.io"
    assert out["reply_content"] == "Sounds good"


def test_lemlist_shape_lifts_top_level_fields() -> None:
    body = {
        "type": "emailsClicked",
        "campaignId": "camp1",
        "campaignName": "Q3",
        "leadEmail": "p@x.io",
        "firstName": "Alice",
        "date": "2026-07-04T12:00:00Z",
    }
    out = lemlist_shape(body, "emailsClicked", "d2")
    assert out["campaign_id"] == "camp1"
    assert out["lead_email"] == "p@x.io"
    assert out["lead_first_name"] == "Alice"


def test_emailbison_shape_handles_nested_data() -> None:
    body = {
        "event": "email_bounced",
        "workspace_id": "ws1",
        "timestamp": "2026-07-04T12:00:00Z",
        "data": {
            "campaign_id": "camp1",
            "lead_id": "lead1",
            "email": "p@x.io",
            "message_id": "msg1",
        },
    }
    out = emailbison_shape(body, "email_bounced", "d3")
    assert out["event"] == "email_bounced"
    assert out["campaign_id"] == "camp1"
    assert out["lead_email"] == "p@x.io"
    assert out["message_id"] == "msg1"


# ── credentials registered ───────────────────────────────────────────


def test_lemlist_emailbison_credentials_registered() -> None:
    from apps.api.app.credential_manager.api_keys import PROVIDERS

    assert "lemlist" in PROVIDERS
    assert "emailbison" in PROVIDERS
