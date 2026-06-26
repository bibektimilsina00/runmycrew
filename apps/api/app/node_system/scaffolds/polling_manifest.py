"""Manifest schema for the polling-trigger scaffold.

A polling trigger polls some REST endpoint on a cadence and emits one
workflow execution per *new* item since the last cursor. The manifest
describes:

  - **Brand identity** + auth scheme (reuses the REST scaffold's
    auth types so a provider's polling trigger and action node share
    one credential model).
  - **Common fields** that apply across every event (`owner`, `repo`,
    `max_per_poll`, `poll_interval_seconds`, …).
  - **Per-event manifests** — list URL, optional static params, cursor
    strategy, output flattener.

The factory in `polling_node_factory.py` turns a manifest into a
`BaseNode` that the scheduler can drive. Pure-data manifest means a new
polling integration is dozens of lines, not hundreds.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.node_system.scaffolds.rest_manifest import AuthScheme, FieldSpec

# ── cursor strategies ────────────────────────────────────────────────


CursorStrategy = Literal["known_ids", "since_timestamp", "last_sha"]


# A custom-diff handler runs after a poll fetched items. It owns the
# diff against `cursor`, returns `(matches, new_cursor)`. Drops down to
# this when the three builtin strategies don't fit (e.g. etag map,
# nested history events, page-token chains).
#
# Signature: (items, cursor, props, event_id) -> (matches, new_cursor)
#   - items: raw list the factory pulled from `list_path`
#   - cursor: prior persisted dict (or None on first poll)
#   - props: live node props (for `max_per_poll`, etc.)
#   - event_id: this event's `id` field — handlers can stamp it on cursor
CustomDiff = Callable[
    [list[dict[str, Any]], dict[str, Any] | None, Any, str],
    tuple[list[dict[str, Any]], dict[str, Any]],
]


# ── event + manifest types ───────────────────────────────────────────


class PollingEvent(BaseModel):
    """One event the trigger node can fire on.

    Two forms:

    1. **Builtin diff** — set `strategy` to a recognized cursor type.
       `id_field` controls which response key uniquely identifies an
       item (defaults to `id`). `timestamp_field` controls the field
       used for `since_timestamp`.
    2. **Custom diff** — set `diff_handler` to a callable. `strategy`
       is ignored. Useful for cursors the three builtins don't cover.

    `flatten` names a registered flattener so each emitted match shape
    is consistent across the action node + trigger.

    Optional `extra_fields` lists prop names that appear in the
    inspector only when this event is selected (e.g. `branch` only
    matters for `new_commit`).
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str
    label: str
    list_path: str
    list_params: dict[str, Any] = Field(default_factory=dict)
    strategy: CursorStrategy = "known_ids"
    id_field: str = "id"
    timestamp_field: str = "updated_at"
    flatten: str | None = None
    # Optional pre-filter — receives `(item, props)`, returns truthy to
    # KEEP the item. Used e.g. by GitHub's `new_issue` event to drop
    # PRs that share the same `/issues` endpoint.
    filter_fn: Callable[[dict[str, Any], Any], bool] | None = None
    # Custom diff replaces the builtin. When set, `strategy`/`id_field`/
    # `timestamp_field` are not used.
    diff_handler: CustomDiff | None = None
    # Inspector — names of `common_fields` whose visibility is gated by
    # this event being selected. The factory translates these into
    # `condition: {field: event_type, value: id}` rows.
    extra_fields: list[str] = Field(default_factory=list)


class PollingTriggerManifest(BaseModel):
    """Top-level manifest for a polling trigger node."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    # Identity.
    type: str
    name: str
    category: str = "trigger"
    description: str
    icon_slug: str | None = None
    color: str = "#1c1c1c"

    # Auth (mirrors REST manifest).
    base_url: str
    credential_type: str | list[str]
    token_field: str | list[str] = Field(default_factory=lambda: ["access_token", "api_key"])
    auth: AuthScheme = "bearer"
    auth_header_name: str = "Authorization"
    auth_value_template: str = "Bearer {token}"
    auth_query_param: str = "api_key"
    extra_headers: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = 30.0

    # Scheduler binding. `provider` lands in
    # `integration_trigger_state.provider` so the scheduler can route
    # rows back after a worker restart.
    provider: str
    default_poll_interval_seconds: int = 60
    min_poll_interval_seconds: int = 30
    max_poll_interval_seconds: int = 60 * 60

    # Shared inspector fields — `event_type`, `max_per_poll`,
    # `poll_interval_seconds` are injected by the factory; everything
    # else (`owner`, `repo`, `query`, …) lives here.
    common_fields: list[FieldSpec] = Field(default_factory=list)

    # Events.
    events: list[PollingEvent] = Field(default_factory=list)

    # Outputs schema for inspector + autocomplete.
    outputs_schema: list[dict[str, Any]] = Field(default_factory=list)

    # Optional pre-fetcher that walks paginated responses to gather all
    # items in one logical "poll". Defaults to a single page. Receives
    # `(client, manifest, token, event, props)` and returns the merged
    # list. Most providers can stay with the default; gpeople walks
    # `nextPageToken`, GitHub walks `Link: next`, etc.
    paginate_fn: Callable[..., Awaitable[list[dict[str, Any]]]] | None = None
