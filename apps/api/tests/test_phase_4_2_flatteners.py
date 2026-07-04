"""Unit tests for the Phase 4.2 flatteners.

The paginate_fn's job is straightforward (route by event id, GET/POST,
return the list). What's easy to regress is the flatteners: each one
projects the vendor's raw payload down to the fields the workflow
sees. A schema mismatch there produces a downstream node reading None
instead of the real value — hard to catch without tests.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.jira.trigger_manifest import (
    _flatten_comment as jira_flatten_comment,
)
from apps.api.app.node_system.nodes.jira.trigger_manifest import (
    _flatten_project as jira_flatten_project,
)
from apps.api.app.node_system.nodes.jira.trigger_manifest import (
    _flatten_sprint as jira_flatten_sprint,
)
from apps.api.app.node_system.nodes.jira.trigger_manifest import (
    _flatten_worklog as jira_flatten_worklog,
)
from apps.api.app.node_system.nodes.linear.trigger_manifest import (
    _flatten_cycle,
    _flatten_label,
    _flatten_project,
    _flatten_project_update,
)
from apps.api.app.node_system.nodes.notion.trigger_manifest import (
    _flatten_comment as notion_flatten_comment,
)
from apps.api.app.node_system.nodes.notion.trigger_manifest import (
    _flatten_database as notion_flatten_database,
)

# ── Jira ─────────────────────────────────────────────────────────────


def test_jira_comment_carries_issue_key() -> None:
    """The paginate_fn stamps `_issue_key` on each comment so the
    workflow knows *which* issue the comment belongs to — comments
    endpoint doesn't include it natively."""
    comment = {
        "id": "10001",
        "body": "Looks good",
        "author": {"displayName": "Alice", "emailAddress": "a@x.io"},
        "created": "2026-07-04T12:00:00Z",
        "updated": "2026-07-04T12:00:00Z",
        "_issue_key": "ABC-42",
    }
    out = jira_flatten_comment(comment)
    assert out["issue_key"] == "ABC-42"
    assert out["author_name"] == "Alice"
    assert out["author_email"] == "a@x.io"


def test_jira_worklog_carries_time_and_issue() -> None:
    log = {
        "id": "20001",
        "comment": "1h coding",
        "timeSpent": "1h",
        "timeSpentSeconds": 3600,
        "author": {"displayName": "Bob"},
        "started": "2026-07-04T09:00:00Z",
        "_issue_key": "ABC-42",
    }
    out = jira_flatten_worklog(log)
    assert out["time_spent_seconds"] == 3600
    assert out["issue_key"] == "ABC-42"
    assert out["author_name"] == "Bob"


def test_jira_sprint_carries_dates_and_state() -> None:
    sprint = {
        "id": 7,
        "name": "Sprint 7",
        "state": "closed",
        "startDate": "2026-06-01",
        "endDate": "2026-06-15",
        "completeDate": "2026-06-14",
        "originBoardId": 3,
    }
    out = jira_flatten_sprint(sprint)
    assert out["state"] == "closed"
    assert out["board_id"] == 3
    assert out["complete_date"] == "2026-06-14"


def test_jira_project_flattens_lead_and_type() -> None:
    p = {
        "id": "10000",
        "key": "ABC",
        "name": "Alpha Beta Ceta",
        "projectTypeKey": "software",
        "lead": {"displayName": "Alice"},
        "self": "https://x.atlassian.net/rest/api/3/project/10000",
    }
    out = jira_flatten_project(p)
    assert out["project_type"] == "software"
    assert out["lead"] == "Alice"


# ── Linear ───────────────────────────────────────────────────────────


def test_linear_cycle_hoists_team_key_only() -> None:
    c = {
        "id": "c1",
        "name": "Cycle 1",
        "number": 1,
        "startsAt": "2026-07-01",
        "endsAt": "2026-07-14",
        "team": {"id": "t1", "name": "Team", "key": "TEA"},
    }
    out = _flatten_cycle(c)
    assert out["team_key"] == "TEA"
    assert "team" not in out  # collapsed; only team_key survives


def test_linear_project_carries_url_state_and_lead() -> None:
    p = {
        "id": "p1",
        "name": "Sim Parity",
        "state": "started",
        "url": "https://linear.app/x/p1",
        "lead": {"name": "Alice"},
    }
    out = _flatten_project(p)
    assert out["state"] == "started"
    assert out["lead_name"] == "Alice"
    assert out["url"].endswith("p1")


def test_linear_project_update_pulls_project_ref() -> None:
    """Project updates carry a nested project reference — the flatten
    must surface the project name at the top so the downstream node
    doesn't need to reach into a nested object."""
    u = {
        "id": "u1",
        "body": "On track",
        "health": "onTrack",
        "user": {"name": "Alice"},
        "project": {"id": "p1", "name": "Sim Parity", "url": "https://linear.app/x/p1"},
    }
    out = _flatten_project_update(u)
    assert out["project_name"] == "Sim Parity"
    assert out["health"] == "onTrack"


def test_linear_label_captures_color_and_team() -> None:
    label = {
        "id": "l1",
        "name": "bug",
        "color": "#f00",
        "team": {"key": "TEA"},
    }
    out = _flatten_label(label)
    assert out["color"] == "#f00"
    assert out["team_key"] == "TEA"


# ── Notion ────────────────────────────────────────────────────────────


def test_notion_comment_extracts_text_and_page_id() -> None:
    """Comment payload's `parent.page_id` is what workflow steps need
    to correlate a comment back to its page. Test the fall-through when
    only `block_id` is present (Notion uses one or the other)."""
    with_page = {
        "id": "c1",
        "rich_text": [{"plain_text": "hey "}, {"plain_text": "there"}],
        "parent": {"page_id": "p42"},
        "created_by": {"id": "u1"},
    }
    out = notion_flatten_comment(with_page)
    assert out["text"] == "hey there"
    assert out["page_id"] == "p42"

    with_block = {
        "id": "c2",
        "rich_text": [{"plain_text": "hi"}],
        "parent": {"block_id": "b7"},
        "created_by": {"id": "u1"},
    }
    assert notion_flatten_comment(with_block)["page_id"] == "b7"


def test_notion_database_extracts_title_from_rich_text() -> None:
    db = {
        "id": "d1",
        "title": [{"plain_text": "Tasks "}, {"plain_text": "2026"}],
        "url": "https://notion.so/d1",
        "created_time": "2026-01-01T00:00:00Z",
    }
    out = notion_flatten_database(db)
    assert out["title"] == "Tasks 2026"
