"""Unit tests for Phase 3.5 trigger completions (monday, rss, imap).

Focus on the pieces that would silently regress without a test:
  - The custom-diff handlers for Monday (status/group/columns) —
    they hold the semantics of what "status changed" means.
  - The RSS parser branches — RSS 2.0 vs Atom 1.0 vs RSS 1.0 (RDF).
  - The no-auth scaffold branch — RSS is the first polling provider
    without a credential; a regression there breaks it silently.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from apps.api.app.node_system.nodes.monday.trigger_manifest import (
    _diff_columns,
    _diff_group,
    _diff_status,
)
from apps.api.app.node_system.nodes.rss.trigger_manifest import (
    _parse_atom_entry,
    _parse_rss_item,
)


class _Props:
    """Stub for node.props — Monday diff handlers only read `board_id`."""

    def __init__(self, board_id: str = "b1") -> None:
        self.board_id = board_id


# ── Monday custom diffs ──────────────────────────────────────────────


def _item(item_id: str, status: str = "", group: str = "", cols: list | None = None) -> dict:
    """Build a Monday item shape mirroring what the GraphQL query returns."""
    column_values = list(cols) if cols else []
    if status:
        column_values.insert(
            0,
            {
                "id": "status",
                "text": status,
                "value": f'{{"index":0,"label":{status!r}}}',
                "column": {"id": "status", "title": "Status", "type": "status"},
            },
        )
    return {
        "id": item_id,
        "name": f"item-{item_id}",
        "state": "active",
        "group": {"id": group or "g0", "title": "Group 0"},
        "column_values": column_values,
        "creator": {"id": "u1", "name": "user"},
    }


def test_monday_status_first_poll_snapshots_silently() -> None:
    """First poll on a fresh cursor must NOT flood the workflow with
    every existing item — otherwise activation fires N times."""
    items = [_item("1", status="Working"), _item("2", status="Done")]
    matches, cursor = _diff_status(items, None, _Props(), "status_changed")
    assert matches == []
    assert cursor["values"] == {"1": "Working", "2": "Done"}


def test_monday_status_change_fires() -> None:
    prior = {
        "event_type": "status_changed",
        "board_id": "b1",
        "values": {"1": "Working", "2": "Done"},
    }
    items = [_item("1", status="Done"), _item("2", status="Done")]
    matches, cursor = _diff_status(items, prior, _Props(), "status_changed")
    assert len(matches) == 1
    assert matches[0]["id"] == "1"
    assert matches[0]["change"] == {"key": "status", "from": "Working", "to": "Done"}
    assert cursor["values"]["1"] == "Done"


def test_monday_group_move_fires_once() -> None:
    prior = {
        "event_type": "item_moved",
        "board_id": "b1",
        "values": {"1": "g0", "2": "g0"},
    }
    items = [_item("1", group="g1"), _item("2", group="g0")]
    matches, cursor = _diff_group(items, prior, _Props(), "item_moved")
    assert len(matches) == 1
    assert matches[0]["id"] == "1"
    assert matches[0]["change"] == {"key": "group", "from": "g0", "to": "g1"}
    assert cursor["values"] == {"1": "g1", "2": "g0"}


def test_monday_columns_change_fingerprint() -> None:
    """Column change fires on any column value delta — the fingerprint
    is sort-stable, so column reordering in the API response doesn't
    generate false positives."""
    cols_b = [
        {"id": "num", "text": "1", "column": {"id": "num", "type": "numbers"}},
        {"id": "text", "text": "hello", "column": {"id": "text", "type": "text"}},
    ]  # cursor was primed with text-first ordering; test the reverse order
    prior = {
        "event_type": "column_changed",
        "board_id": "b1",
        "values": {"1": "num=1|text=hello"},
    }
    # Reorder alone should NOT fire.
    matches, _ = _diff_columns([_item("1", cols=cols_b)], prior, _Props(), "column_changed")
    assert matches == []
    # Real value change SHOULD fire.
    cols_c = [{"id": "text", "text": "world", "column": {"id": "text", "type": "text"}}]
    matches2, _ = _diff_columns([_item("1", cols=cols_c)], prior, _Props(), "column_changed")
    assert len(matches2) == 1


def test_monday_board_swap_resets_cursor() -> None:
    """Prior cursor from a different board_id must be treated as
    fresh — otherwise switching boards would emit false "changes" on
    every id."""
    prior = {"event_type": "status_changed", "board_id": "OTHER", "values": {"1": "old"}}
    items = [_item("1", status="new")]
    matches, cursor = _diff_status(items, prior, _Props("b1"), "status_changed")
    assert matches == []  # first poll on the new board — silent snapshot
    assert cursor["board_id"] == "b1"


# ── RSS parser ───────────────────────────────────────────────────────


def test_rss2_item_pulls_guid_and_link() -> None:
    xml = """
      <item>
        <title>Hello</title>
        <link>https://example.com/1</link>
        <description>d</description>
        <pubDate>Mon, 01 Jul 2026 12:00:00 GMT</pubDate>
        <guid>id-1</guid>
        <category>news</category>
      </item>
    """.strip()
    item = ET.fromstring(xml)
    row = _parse_rss_item(item)
    assert row["id"] == "id-1"
    assert row["link"] == "https://example.com/1"
    assert row["categories"] == ["news"]


def test_atom_entry_uses_alternate_link_over_first() -> None:
    """Atom entries can carry multiple <link> elements — the alternate
    is the human-facing URL; edit links etc. shouldn't win."""
    xml = """
      <entry xmlns="http://www.w3.org/2005/Atom">
        <id>urn:x:1</id>
        <title>Atom</title>
        <link href="https://example.com/edit" rel="edit"/>
        <link href="https://example.com/view" rel="alternate"/>
        <summary>s</summary>
        <published>2026-07-01T12:00:00Z</published>
        <author><name>Alice</name></author>
      </entry>
    """.strip()
    entry = ET.fromstring(xml)
    row = _parse_atom_entry(entry)
    assert row["link"] == "https://example.com/view"
    assert row["author"] == "Alice"


def test_rss_item_falls_back_to_link_when_no_guid() -> None:
    xml = """
      <item>
        <title>t</title>
        <link>https://example.com/no-guid</link>
      </item>
    """.strip()
    item = ET.fromstring(xml)
    row = _parse_rss_item(item)
    assert row["id"] == "https://example.com/no-guid"


# ── No-auth scaffold branch ──────────────────────────────────────────


def test_rss_registers_as_unauthenticated_provider() -> None:
    """The scheduler treats `token_fields=[]` as "no cred lookup" — a
    regression that resets that default breaks RSS silently, since
    the scheduler would then 401 on missing access_token."""
    from apps.api.app.execution_engine.scheduler.integration_polling import (
        _BY_PROVIDER,
        eager_register_polling_providers,
    )

    eager_register_polling_providers()
    entry = _BY_PROVIDER.get("rss")
    assert entry is not None
    assert entry.token_fields == []


def test_rss_manifest_credential_type_is_none() -> None:
    """The factory reads `credential_type is None` to skip the
    credential inspector row + skip the cred-required error path."""
    from apps.api.app.node_system.nodes.rss.trigger_manifest import MANIFEST

    assert MANIFEST.credential_type is None
    assert MANIFEST.token_field == []
