"""Unit tests for Phase 4.8 outbound-email providers.

Covers instantly's two custom diffs (lead status change, campaign
completed) + emailbison flatteners + credential registration.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.emailbison.trigger_manifest import (
    _flatten_campaign as eb_flatten_campaign,
)
from apps.api.app.node_system.nodes.emailbison.trigger_manifest import (
    _flatten_lead as eb_flatten_lead,
)
from apps.api.app.node_system.nodes.instantly.trigger_manifest import (
    _diff_campaign_completed,
    _diff_lead_status_change,
)
from apps.api.app.node_system.nodes.instantly.trigger_manifest import (
    _flatten_campaign as ins_flatten_campaign,
)
from apps.api.app.node_system.nodes.instantly.trigger_manifest import (
    _flatten_lead as ins_flatten_lead,
)

# ── Instantly: lead_status_changed diff ─────────────────────────────


class _Props:
    def __init__(self, campaign_id: str = "") -> None:
        self.campaign_id = campaign_id


def _lead(lid: str, status: int, **extra) -> dict:
    return {"id": lid, "status": status, "email": f"{lid}@x.io", **extra}


def test_instantly_lead_status_first_poll_snapshots() -> None:
    """First poll must not fire on every existing lead — otherwise
    workflow activation floods with N events."""
    matches, cursor = _diff_lead_status_change(
        [_lead("l1", 1), _lead("l2", 2)], None, _Props(), "lead_status_changed"
    )
    assert matches == []
    assert cursor["statuses"] == {"l1": 1, "l2": 2}


def test_instantly_lead_status_fires_on_transition() -> None:
    prior = {
        "event_type": "lead_status_changed",
        "campaign_id": "",
        "statuses": {"l1": 1, "l2": 2},
    }
    items = [_lead("l1", 3), _lead("l2", 2)]  # l1 moved 1→3
    matches, cursor = _diff_lead_status_change(items, prior, _Props(), "lead_status_changed")
    assert len(matches) == 1
    assert matches[0]["id"] == "l1"
    assert matches[0]["change"] == {"key": "status", "from": 1, "to": 3}
    assert cursor["statuses"]["l1"] == 3


def test_instantly_lead_status_campaign_swap_resets() -> None:
    """Switching campaign_id invalidates prior status map — else a
    fresh scope would replay every existing lead's status as a change."""
    prior = {
        "event_type": "lead_status_changed",
        "campaign_id": "OTHER",
        "statuses": {"l1": 1},
    }
    matches, cursor = _diff_lead_status_change(
        [_lead("l1", 3)], prior, _Props("current"), "lead_status_changed"
    )
    assert matches == []  # first poll on new scope
    assert cursor["campaign_id"] == "current"


# ── Instantly: campaign_completed diff ──────────────────────────────


def test_instantly_campaign_completed_fires_only_on_transition_to_3() -> None:
    """Emit only when campaign status transitions INTO 3 (completed).
    A campaign that was already completed on the first poll should not
    fire on the second poll either."""
    prior = {
        "event_type": "campaign_completed",
        "statuses": {"c1": 1, "c2": 3},  # c2 already completed
    }
    items = [
        {"id": "c1", "status": 3, "name": "New Q3"},  # 1 → 3, fire
        {"id": "c2", "status": 3, "name": "Old Q2"},  # 3 → 3, no fire
    ]
    matches, cursor = _diff_campaign_completed(items, prior, _Props(), "campaign_completed")
    ids = [m["id"] for m in matches]
    assert ids == ["c1"]
    assert cursor["statuses"] == {"c1": 3, "c2": 3}


def test_instantly_campaign_completed_first_poll_snapshots() -> None:
    matches, cursor = _diff_campaign_completed(
        [{"id": "c1", "status": 1}, {"id": "c2", "status": 3}],
        None,
        _Props(),
        "campaign_completed",
    )
    assert matches == []
    assert cursor["statuses"] == {"c1": 1, "c2": 3}


# ── Flatteners ──────────────────────────────────────────────────────


def test_instantly_lead_flatten_carries_engagement_flags() -> None:
    lead = {
        "id": "l1",
        "email": "p@x.io",
        "first_name": "Alice",
        "status": 2,
        "campaign": "camp1",
        "email_opened": True,
        "email_clicked": False,
        "email_replied": True,
        "timestamp_created": "2026-07-01T09:00:00Z",
    }
    out = ins_flatten_lead(lead)
    assert out["campaign_id"] == "camp1"
    assert out["email_opened"] is True
    assert out["email_replied"] is True
    assert out["created_at"] == "2026-07-01T09:00:00Z"


def test_instantly_campaign_flatten() -> None:
    c = {
        "id": "c1",
        "name": "Q3 Outbound",
        "status": 1,
        "timestamp_created": "2026-07-01T00:00:00Z",
    }
    out = ins_flatten_campaign(c)
    assert out["name"] == "Q3 Outbound"
    assert out["status"] == 1


def test_emailbison_flatteners() -> None:
    lead_out = eb_flatten_lead(
        {
            "id": "l1",
            "email": "p@x.io",
            "first_name": "Alice",
            "campaign_id": "camp1",
            "status": "active",
            "created_at": "2026-07-01T09:00:00Z",
        }
    )
    assert lead_out["email"] == "p@x.io"
    assert lead_out["campaign_id"] == "camp1"

    camp_out = eb_flatten_campaign(
        {
            "id": "c1",
            "name": "Q3",
            "status": "active",
            "workspace_id": "ws1",
        }
    )
    assert camp_out["workspace_id"] == "ws1"


# ── Credentials + trigger events ────────────────────────────────────


def test_outbound_credentials_registered() -> None:
    from apps.api.app.credential_manager.api_keys import PROVIDERS

    assert "emailbison" in PROVIDERS
    assert {f.id for f in PROVIDERS["emailbison"].fields} == {"api_key"}


def test_instantly_manifest_covers_expected_events() -> None:
    from apps.api.app.node_system.nodes.instantly.trigger_manifest import MANIFEST

    ids = {e.id for e in MANIFEST.events}
    assert ids == {"new_lead", "lead_status_changed", "campaign_completed"}


def test_emailbison_manifest_covers_expected_events() -> None:
    from apps.api.app.node_system.nodes.emailbison.trigger_manifest import MANIFEST

    ids = {e.id for e in MANIFEST.events}
    assert ids == {"new_lead", "new_campaign"}
