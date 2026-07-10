"""Unit tests for the template marketplace service helpers.

Focuses on the pure-function pieces that ship as part of the publish
flow: slug generation + graph scrubbing. The DB-bound integration
paths (install gate, marketplace filtering) are covered by manual
verification against the seeded loop templates + the existing E2E
test plan — running them in unit tests requires aiosqlite which is
not currently in the project's runtime deps.
"""

from __future__ import annotations

from apps.api.app.features.templates.service import (
    _prepare_graph_snapshot,
    _slugify,
)

# ── Slugify ────────────────────────────────────────────────────────


def test_slugify_handles_underscores_and_unicode():
    assert _slugify("loop_linear_triage") == "loop-linear-triage"
    assert _slugify("Sentry → GitHub issue") == "sentry-github-issue"
    assert _slugify("   Triage new Linear bugs!  ") == "triage-new-linear-bugs"


def test_slugify_empty_falls_back_to_template():
    assert _slugify("!!!") == "template"
    assert _slugify("") == "template"


# ── Graph scrubbing ────────────────────────────────────────────────


def test_prepare_graph_strips_credential_ids():
    raw = {
        "nodes": [
            {
                "id": "agent",
                "type": "action.agent",
                "data": {
                    "properties": {
                        "credential": "cred_abc",
                        "model": "claude-sonnet",
                    }
                },
            },
            {
                "id": "slack",
                "type": "action.slack",
                "data": {
                    "properties": {
                        "credential_id": "cred_xyz",
                        "channel": "#oncall",
                    }
                },
            },
        ],
        "edges": [],
    }
    snapshot, creds, tools = _prepare_graph_snapshot(raw)
    # Original input is untouched.
    assert raw["nodes"][0]["data"]["properties"]["credential"] == "cred_abc"
    # Snapshot has the secrets scrubbed.
    assert snapshot["nodes"][0]["data"]["properties"]["credential"] == ""
    assert snapshot["nodes"][1]["data"]["properties"]["credential_id"] == ""
    # Required lists derived from the graph. Only credentialed nodes count
    # as integrations — action.agent is a core node, not a tool chip.
    assert "slack" in tools and "agent" not in tools
    assert len(creds) >= 1


def test_prepare_graph_handles_empty_input():
    snapshot, creds, tools = _prepare_graph_snapshot({})
    assert snapshot == {"nodes": [], "edges": []}
    assert creds == []
    assert tools == []


def test_prepare_graph_picks_up_camelcase_credential_field():
    raw = {
        "nodes": [
            {
                "id": "agent",
                "type": "action.agent",
                "data": {
                    "properties": {
                        "anthropicCredential": "cred_camel",
                        "model": "claude-sonnet",
                    }
                },
            }
        ],
        "edges": [],
    }
    snapshot, _creds, _tools = _prepare_graph_snapshot(raw)
    assert snapshot["nodes"][0]["data"]["properties"]["anthropicCredential"] == ""
