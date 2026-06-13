"""Tests for the agent's workflow-as-tool schema build + name mapping (PR 5.5).

The agent serialises `workflow:<uuid>` saved entries into OpenAI function
schemas with an LLM-safe name (`workflow_<uuid>` — colons aren't allowed)
and tracks a reverse mapping so tool-call dispatch can translate the
LLM's name back to the saved tool_id before any state lookup.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.ai.agent.agent import AgentNode

# ──────────────────────────────────────────────────────────────────────────
#  Safe-name conversion
# ──────────────────────────────────────────────────────────────────────────


def test_workflow_safe_name_replaces_colon() -> None:
    # OpenAI rejects function names containing `:`; we strip it.
    safe = AgentNode._workflow_tool_safe_name("workflow:abc12345-1234-1234-1234-1234567890ab")
    assert safe == "workflow_abc12345-1234-1234-1234-1234567890ab"


def test_workflow_safe_name_is_identity_for_non_workflow_ids() -> None:
    # The transform is a single colon-to-underscore — non-workflow tool ids
    # (no colons in practice) pass through unchanged.
    assert AgentNode._workflow_tool_safe_name("slack_send_message") == "slack_send_message"


# ──────────────────────────────────────────────────────────────────────────
#  Schema build from saved snapshot
# ──────────────────────────────────────────────────────────────────────────


def test_workflow_tool_schema_uses_saved_snapshot() -> None:
    entry = {
        "toolId": "workflow:abc",
        "name": "Summarise email",
        "description": "Take a subject + body, produce a one-line summary.",
        "paramsSchema": {
            "subject": {
                "type": "string",
                "required": True,
                "description": "Email subject line",
            },
            "body": {"type": "string", "required": True, "description": ""},
            "priority": {"type": "number", "required": False, "description": ""},
        },
    }
    schema = AgentNode._build_workflow_tool_schema("workflow:abc", entry)
    function = schema["function"]
    assert function["name"] == "workflow_abc"
    assert function["description"] == entry["description"]

    params = function["parameters"]
    assert params["type"] == "object"
    # Ordering of required reflects insertion order of the schema dict.
    assert set(params["required"]) == {"subject", "body"}
    assert params["properties"]["subject"]["type"] == "string"
    assert params["properties"]["subject"]["description"] == "Email subject line"
    assert params["properties"]["priority"]["type"] == "number"


def test_workflow_tool_schema_falls_back_to_empty_when_no_snapshot() -> None:
    # Saved entry without a paramsSchema snapshot — the schema still
    # builds (empty-object) so the LLM can call it; user-preset params
    # from the inspector will merge in regardless.
    schema = AgentNode._build_workflow_tool_schema("workflow:abc", {"toolId": "workflow:abc"})
    params = schema["function"]["parameters"]
    assert params == {"type": "object", "properties": {}, "required": []}


def test_workflow_tool_schema_json_type_maps_to_object() -> None:
    schema = AgentNode._build_workflow_tool_schema(
        "workflow:abc",
        {
            "toolId": "workflow:abc",
            "paramsSchema": {"payload": {"type": "json", "required": False, "description": ""}},
        },
    )
    # OpenAI's JSON-Schema only knows `object`, not `json` — we translate.
    assert schema["function"]["parameters"]["properties"]["payload"]["type"] == "object"


def test_workflow_tool_schema_default_description_uses_display_name() -> None:
    schema = AgentNode._build_workflow_tool_schema(
        "workflow:abc",
        {"toolId": "workflow:abc", "name": "My Workflow"},
    )
    assert "My Workflow" in schema["function"]["description"]
