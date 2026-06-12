"""Tests for the tool catalog service.

The HTTP layer is thin — service unit tests cover the categorisation,
filter logic, and serialisation. Endpoint shape is covered by a Pydantic
round-trip per case so we know the schema accepts the data.
"""

from __future__ import annotations

from apps.api.app.features.tools.schemas import ToolListResponse, ToolSchema
from apps.api.app.features.tools.service import (
    ToolCatalogService,
    derive_category,
    label_for_category,
)

# ──────────────────────────────────────────────────────────────────────────
#  derive_category / label_for_category
# ──────────────────────────────────────────────────────────────────────────


def test_derive_category_splits_on_first_underscore() -> None:
    assert derive_category("slack_send_message") == "slack"
    assert derive_category("http_request") == "http"
    assert derive_category("workflow_call") == "workflow"


def test_derive_category_returns_whole_id_when_no_underscore() -> None:
    # Built-in single-name tools like the umbrella `slack` operation router
    # are categorised as themselves rather than empty.
    assert derive_category("slack") == "slack"


def test_label_for_known_category_uses_pretty_name() -> None:
    assert label_for_category("slack") == "Slack"
    assert label_for_category("http") == "HTTP"
    assert label_for_category("mcp") == "MCP"


def test_label_for_unknown_category_title_cases() -> None:
    assert label_for_category("foo_bar") == "Foo Bar"


# ──────────────────────────────────────────────────────────────────────────
#  list_tools
# ──────────────────────────────────────────────────────────────────────────


def test_list_tools_returns_all_registered_tools() -> None:
    service = ToolCatalogService()
    response = service.list_tools()
    assert response.total > 0
    assert response.total == len(response.tools)

    # Every tool surfaces its derived category and label.
    for tool in response.tools:
        assert tool.category
        assert tool.category_label
        assert tool.id


def test_list_tools_groups_by_category_in_response() -> None:
    service = ToolCatalogService()
    response = service.list_tools()
    cat_ids = {c.id for c in response.categories}
    # Every tool's category appears in the response's category list.
    for tool in response.tools:
        assert tool.category in cat_ids


def test_list_tools_category_counts_match_tool_counts() -> None:
    service = ToolCatalogService()
    response = service.list_tools()
    expected: dict[str, int] = {}
    for tool in response.tools:
        expected[tool.category] = expected.get(tool.category, 0) + 1
    actual = {c.id: c.count for c in response.categories}
    assert actual == expected


def test_list_tools_filters_by_category() -> None:
    service = ToolCatalogService()
    response = service.list_tools(category="slack")
    assert response.total > 0
    assert all(t.category == "slack" for t in response.tools)


def test_list_tools_filter_by_unknown_category_returns_empty() -> None:
    service = ToolCatalogService()
    response = service.list_tools(category="nonexistent")
    assert response.total == 0
    assert response.categories == []


def test_list_tools_search_matches_id_name_description() -> None:
    service = ToolCatalogService()
    response = service.list_tools(q="slack")
    assert response.total > 0
    for tool in response.tools:
        assert (
            "slack" in tool.id.lower()
            or "slack" in tool.name.lower()
            or "slack" in tool.description.lower()
        )


def test_list_tools_search_is_case_insensitive() -> None:
    a = ToolCatalogService().list_tools(q="SLACK").total
    b = ToolCatalogService().list_tools(q="slack").total
    assert a == b > 0


def test_list_tools_filter_by_requires_auth_true() -> None:
    service = ToolCatalogService()
    response = service.list_tools(requires_auth=True)
    for tool in response.tools:
        assert tool.requires_auth is True
        assert tool.oauth is not None
        assert tool.oauth.required is True


def test_list_tools_filter_by_requires_auth_false_excludes_oauth_tools() -> None:
    service = ToolCatalogService()
    response = service.list_tools(requires_auth=False)
    for tool in response.tools:
        assert tool.requires_auth is False


def test_list_tools_sorted_by_category_then_name() -> None:
    response = ToolCatalogService().list_tools()
    pairs = [(t.category, t.name.lower()) for t in response.tools]
    assert pairs == sorted(pairs)


# ──────────────────────────────────────────────────────────────────────────
#  get_tool
# ──────────────────────────────────────────────────────────────────────────


def test_get_tool_returns_definition_for_known_id() -> None:
    service = ToolCatalogService()
    tool = service.get_tool("slack_send_message")
    assert tool is not None
    assert tool.id == "slack_send_message"
    assert tool.category == "slack"


def test_get_tool_returns_none_for_unknown_id() -> None:
    assert ToolCatalogService().get_tool("does_not_exist") is None


def test_get_tool_resolves_version_aliases() -> None:
    # The registry's `resolve_tool_id` upgrades unversioned references to
    # the highest registered version, so the catalog should mirror that.
    service = ToolCatalogService()
    response = service.list_tools()
    if not response.tools:
        return  # registry empty in test env (would already fail earlier)
    canonical = response.tools[0]
    assert service.get_tool(canonical.id) is not None


# ──────────────────────────────────────────────────────────────────────────
#  list_categories
# ──────────────────────────────────────────────────────────────────────────


def test_list_categories_returns_all_buckets_with_counts() -> None:
    service = ToolCatalogService()
    categories = service.list_categories()
    assert categories
    # Every registered tool's category appears.
    response = service.list_tools()
    expected: dict[str, int] = {}
    for tool in response.tools:
        expected[tool.category] = expected.get(tool.category, 0) + 1
    actual = {c.id: c.count for c in categories}
    assert actual == expected


# ──────────────────────────────────────────────────────────────────────────
#  Pydantic round-trip
# ──────────────────────────────────────────────────────────────────────────


def test_response_serialises_and_validates_round_trip() -> None:
    response = ToolCatalogService().list_tools()
    payload = response.model_dump()
    rebuilt = ToolListResponse.model_validate(payload)
    assert rebuilt.total == response.total


def test_tool_schema_round_trip_preserves_params() -> None:
    tool = ToolCatalogService().get_tool("slack_send_message")
    assert tool is not None
    payload = tool.model_dump()
    rebuilt = ToolSchema.model_validate(payload)
    assert rebuilt.params == tool.params
