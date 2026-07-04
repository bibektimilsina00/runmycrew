"""Unit tests for the Phase 4.3 trigger providers (attio + salesforce).

Attio flatteners collapse a nested-versioned values envelope into flat
key/value pairs — schema drift there silently loses workflow data.
Salesforce's opportunity-stage-changed diff is fully custom (no builtin
strategy fits per-item field tracking), so we exercise its snapshot +
change-detection semantics directly.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.attio.trigger_manifest import (
    _flatten_list_entry,
    _flatten_member,
    _flatten_note,
    _flatten_record,
    _flatten_task,
    _pull_id,
    _stamp_ids,
)
from apps.api.app.node_system.nodes.salesforce.trigger_manifest import (
    _diff_stage_changed,
)
from apps.api.app.node_system.nodes.salesforce.trigger_manifest import (
    _flatten_record as sf_flatten_record,
)


class _Props:
    def __init__(self, object_type: str = "Opportunity") -> None:
        self.object_type = object_type


# ── Attio: id extraction ─────────────────────────────────────────────


def test_attio_pull_id_walks_multiple_key_names() -> None:
    """Attio's `id` envelope carries different keys per entity type —
    a shared pull helper hides that from downstream."""
    assert _pull_id({"id": {"record_id": "r1"}}) == "r1"
    assert _pull_id({"id": {"entry_id": "e2"}}) == "e2"
    assert _pull_id({"id": {"task_id": "t3"}}) == "t3"
    assert _pull_id({"id": {"comment_id": "c4"}}) == "c4"
    assert _pull_id({"id": {"workspace_member_id": "m5"}}) == "m5"
    assert _pull_id({"id": "plain-string"}) == "plain-string"
    assert _pull_id({"id": {}}) == ""
    assert _pull_id({}) == ""


def test_attio_stamp_ids_hoists_stable_id_string() -> None:
    """`known_ids` diff reads `item[id_field]` on the raw item. Attio
    ships id as a nested object — the paginate_fn must hoist a flat
    string so the scaffold's diff can key on it."""
    items = [
        {"id": {"record_id": "r1"}, "name": "a"},
        {"id": {"record_id": "r2"}, "name": "b"},
    ]
    stamped = _stamp_ids(items)
    assert stamped[0]["id"] == "r1"
    assert stamped[1]["id"] == "r2"


# ── Attio: value collapse ────────────────────────────────────────────


def test_attio_record_collapses_versioned_values() -> None:
    """Attio wraps every field in an array of versions. The flatten
    picks the first (most recent) version and hoists its scalar value
    so the workflow sees `record.values.company == "Acme"` not
    `record.values.company[0].value`."""
    record = {
        "id": {"record_id": "r1", "object_slug": "people"},
        "created_at": "2026-07-01T12:00:00Z",
        "updated_at": "2026-07-04T09:00:00Z",
        "web_url": "https://app.attio.com/r/r1",
        "values": {
            "name": [{"value": "Alice"}],
            "primary_email_address": [{"email_address": "alice@x.io"}],
            "company": [{"target_record": {"record_id": "c1"}}],
        },
    }
    out = _flatten_record(record)
    assert out["id"] == "r1"
    assert out["object_slug"] == "people"
    assert out["values"]["name"] == "Alice"
    assert out["values"]["primary_email_address"] == "alice@x.io"
    assert out["values"]["company"] == {"record_id": "c1"}


def test_attio_list_entry_carries_parent_record() -> None:
    """Parent record info is what the workflow needs to correlate a
    list-entry event back to the owning record."""
    entry = {
        "id": {"entry_id": "e1", "list_id": "l1"},
        "parent_record_id": "r1",
        "parent_object": "companies",
        "created_at": "2026-07-04T10:00:00Z",
    }
    out = _flatten_list_entry(entry)
    assert out["id"] == "e1"
    assert out["parent_record_id"] == "r1"
    assert out["parent_object"] == "companies"
    assert out["list_id"] == "l1"


def test_attio_note_task_member_flatten() -> None:
    n = _flatten_note(
        {
            "id": {"note_id": "n1"},
            "title": "hi",
            "content_plaintext": "body",
            "parent_object": "people",
            "parent_record_id": "r1",
        }
    )
    assert n["id"] == "n1"
    assert n["content_plaintext"] == "body"

    t = _flatten_task(
        {
            "id": {"task_id": "t1"},
            "content_plaintext": "follow up",
            "is_completed": False,
        }
    )
    assert t["id"] == "t1"
    assert t["is_completed"] is False

    m = _flatten_member(
        {
            "id": {"workspace_member_id": "m1"},
            "first_name": "Bob",
            "email_address": "b@x.io",
            "access_level": "admin",
        }
    )
    assert m["id"] == "m1"
    assert m["access_level"] == "admin"


# ── Salesforce: opportunity_stage_changed custom diff ────────────────


def _opp(id_: str, stage: str) -> dict:
    return {
        "Id": id_,
        "Name": f"Opp {id_}",
        "StageName": stage,
        "Amount": 1000,
        "LastModifiedDate": "2026-07-04T12:00:00Z",
    }


def test_salesforce_stage_first_poll_snapshots_silent() -> None:
    """First poll must not fire on every existing opportunity — it
    would flood the workflow at activation time."""
    items = [_opp("o1", "Qualification"), _opp("o2", "Prospecting")]
    matches, cursor = _diff_stage_changed(items, None, _Props(), "opportunity_stage_changed")
    assert matches == []
    assert cursor["stages"] == {"o1": "Qualification", "o2": "Prospecting"}


def test_salesforce_stage_fires_on_change() -> None:
    prior = {
        "event_type": "opportunity_stage_changed",
        "object_type": "Opportunity",
        "stages": {"o1": "Qualification", "o2": "Prospecting"},
    }
    items = [_opp("o1", "Closed Won"), _opp("o2", "Prospecting")]
    matches, cursor = _diff_stage_changed(items, prior, _Props(), "opportunity_stage_changed")
    assert len(matches) == 1
    assert matches[0]["id"] == "o1"
    assert matches[0]["change"] == {"key": "StageName", "from": "Qualification", "to": "Closed Won"}
    assert cursor["stages"]["o1"] == "Closed Won"


def test_salesforce_stage_object_swap_resets_cursor() -> None:
    """Switching object_type (Opportunity → Lead) invalidates the
    prior stages map — otherwise a workflow user would see false
    changes when re-scoping the trigger."""
    prior = {
        "event_type": "opportunity_stage_changed",
        "object_type": "Lead",  # different from props
        "stages": {"o1": "Working"},
    }
    items = [_opp("o1", "Closed Won")]
    matches, cursor = _diff_stage_changed(
        items, prior, _Props("Opportunity"), "opportunity_stage_changed"
    )
    assert matches == []  # first poll on new scope
    assert cursor["object_type"] == "Opportunity"


def test_salesforce_record_flatten_hoists_common_fields() -> None:
    """The flatten hoists Name / Amount / StageName / Status so the
    workflow doesn't need SObject-specific field paths."""
    record = {
        "Id": "0061a00000ABC",
        "Name": "Acme Deal",
        "StageName": "Closed Won",
        "Amount": 5000,
        "LastModifiedDate": "2026-07-04T12:00:00Z",
        "CreatedDate": "2026-07-01T09:00:00Z",
        "attributes": {
            "type": "Opportunity",
            "url": "/services/data/v59.0/sobjects/Opportunity/0061a00000ABC",
        },
    }
    out = sf_flatten_record(record)
    assert out["id"] == "0061a00000ABC"
    assert out["type"] == "Opportunity"
    assert out["stage"] == "Closed Won"
    assert out["amount"] == 5000
