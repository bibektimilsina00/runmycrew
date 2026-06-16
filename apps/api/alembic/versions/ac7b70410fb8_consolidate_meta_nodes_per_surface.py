"""consolidate meta nodes per-surface

Revision ID: ac7b70410fb8
Revises: 988837851652
Create Date: 2026-06-14 20:24:43.742312

Rewrites every saved workflow graph + every MetaSubscription row so the
24 per-task Meta nodes collapse into the eight per-surface consolidated
nodes (instagram/facebook/whatsapp/lead × trigger/action). The new nodes
carry an `event_type` or `operation` dropdown — the old per-task node
becomes one preset value on that dropdown.

The rewrite is idempotent: running it twice is a no-op once all rows
already reference the consolidated names.
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ac7b70410fb8"
down_revision: str | None = "988837851652"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Per-task node type → (consolidated node type, dropdown field, dropdown value).
_NODE_TYPE_MAP: dict[str, tuple[str, str, str]] = {
    # Instagram triggers
    "trigger.meta.ig_comment": ("trigger.meta.instagram", "event_type", "comment"),
    "trigger.meta.ig_message": ("trigger.meta.instagram", "event_type", "message"),
    "trigger.meta.ig_mention": ("trigger.meta.instagram", "event_type", "mention"),
    "trigger.meta.ig_story_reply": ("trigger.meta.instagram", "event_type", "story_reply"),
    "trigger.meta.ig_story_mention": ("trigger.meta.instagram", "event_type", "story_mention"),
    # Instagram actions
    "action.meta.ig_send_dm": ("action.meta.instagram", "operation", "send_dm"),
    "action.meta.ig_reply_comment": ("action.meta.instagram", "operation", "reply_comment"),
    "action.meta.ig_publish_post": ("action.meta.instagram", "operation", "publish_post"),
    "action.meta.ig_publish_story": ("action.meta.instagram", "operation", "publish_story"),
    # Facebook / Messenger triggers
    "trigger.meta.fb_comment": ("trigger.meta.facebook", "event_type", "comment"),
    "trigger.meta.fb_message": ("trigger.meta.facebook", "event_type", "message"),
    "trigger.meta.fb_mention": ("trigger.meta.facebook", "event_type", "mention"),
    "trigger.meta.fb_postback": ("trigger.meta.facebook", "event_type", "postback"),
    "trigger.meta.fb_reaction": ("trigger.meta.facebook", "event_type", "reaction"),
    # Facebook actions
    "action.meta.fb_send_message": ("action.meta.facebook", "operation", "send_message"),
    "action.meta.fb_reply_comment": ("action.meta.facebook", "operation", "reply_comment"),
    "action.meta.fb_publish_post": ("action.meta.facebook", "operation", "publish_post"),
    # WhatsApp triggers
    "trigger.meta.wa_message": ("trigger.meta.whatsapp", "event_type", "message"),
    "trigger.meta.wa_status": ("trigger.meta.whatsapp", "event_type", "status"),
    # WhatsApp actions
    "action.meta.wa_send_message": ("action.meta.whatsapp", "operation", "send_text"),
    "action.meta.wa_send_template": ("action.meta.whatsapp", "operation", "send_template"),
    "action.meta.wa_mark_read": ("action.meta.whatsapp", "operation", "mark_read"),
    # Lead Ads
    "trigger.meta.lead_submission": ("trigger.meta.lead", "event_type", "submission"),
    "action.meta.lead_fetch": ("action.meta.lead", "operation", "fetch"),
}

# Property renames so each per-task action's saved property names match
# the consolidated node's Pydantic model.
_PROPERTY_RENAMES: dict[str, dict[str, str]] = {
    "action.meta.ig_reply_comment": {"message": "reply_text"},
    "action.meta.fb_reply_comment": {"message": "reply_text"},
    "action.meta.fb_publish_post": {"message": "post_message"},
}

_CONSOLIDATED_TYPES = {
    "trigger.meta.instagram",
    "action.meta.instagram",
    "trigger.meta.facebook",
    "action.meta.facebook",
    "trigger.meta.whatsapp",
    "action.meta.whatsapp",
    "trigger.meta.lead",
    "action.meta.lead",
}


def _coerce_graph(graph) -> dict | None:
    if graph is None:
        return None
    if isinstance(graph, str):
        try:
            return json.loads(graph)
        except json.JSONDecodeError:
            return None
    if isinstance(graph, dict):
        return graph
    return None


def _rewrite_graph(graph: dict) -> tuple[dict, bool]:
    nodes = graph.get("nodes") or []
    if not isinstance(nodes, list):
        return graph, False

    changed = False
    new_nodes = []
    for node in nodes:
        if not isinstance(node, dict):
            new_nodes.append(node)
            continue
        node_type = str(node.get("type") or "")
        mapping = _NODE_TYPE_MAP.get(node_type)
        if mapping is None:
            new_nodes.append(node)
            continue
        new_type, dropdown_field, dropdown_value = mapping

        data = dict(node.get("data") or {})
        props = dict(data.get("properties") or {})
        for old_key, new_key in _PROPERTY_RENAMES.get(node_type, {}).items():
            if old_key in props and new_key not in props:
                props[new_key] = props.pop(old_key)
        props[dropdown_field] = dropdown_value

        data["properties"] = props
        new_node = dict(node)
        new_node["type"] = new_type
        new_node["data"] = data
        new_nodes.append(new_node)
        changed = True

    if not changed:
        return graph, False
    new_graph = dict(graph)
    new_graph["nodes"] = new_nodes
    return new_graph, True


_DOWNGRADE_MAP: dict[tuple[str, str, str], str] = {
    (new_type, field, value): old_type
    for old_type, (new_type, field, value) in _NODE_TYPE_MAP.items()
}


def _downgrade_graph(graph: dict) -> tuple[dict, bool]:
    nodes = graph.get("nodes") or []
    if not isinstance(nodes, list):
        return graph, False

    changed = False
    new_nodes = []
    for node in nodes:
        if not isinstance(node, dict):
            new_nodes.append(node)
            continue
        node_type = str(node.get("type") or "")
        if node_type not in _CONSOLIDATED_TYPES:
            new_nodes.append(node)
            continue
        props = dict((node.get("data") or {}).get("properties") or {})
        matched = False
        for field in ("event_type", "operation"):
            value = str(props.get(field) or "").strip()
            if not value:
                continue
            old_type = _DOWNGRADE_MAP.get((node_type, field, value))
            if old_type is None:
                continue
            reverse_renames = {
                new_key: old_key for old_key, new_key in _PROPERTY_RENAMES.get(old_type, {}).items()
            }
            for new_key, old_key in reverse_renames.items():
                if new_key in props and old_key not in props:
                    props[old_key] = props.pop(new_key)
            props.pop(field, None)
            data = dict(node.get("data") or {})
            data["properties"] = props
            new_node = dict(node)
            new_node["type"] = old_type
            new_node["data"] = data
            new_nodes.append(new_node)
            changed = True
            matched = True
            break
        if not matched:
            new_nodes.append(node)

    if not changed:
        return graph, False
    new_graph = dict(graph)
    new_graph["nodes"] = new_nodes
    return new_graph, True


def _walk_workflows(rewrite_fn) -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, graph FROM workflow")).fetchall()
    for row in rows:
        workflow_id, raw_graph = row[0], row[1]
        graph = _coerce_graph(raw_graph)
        if graph is None:
            continue
        new_graph, changed = rewrite_fn(graph)
        if not changed:
            continue
        # Bind JSON explicitly so asyncpg / psycopg both accept the dict.
        stmt = sa.text("UPDATE workflow SET graph = :g WHERE id = :id").bindparams(
            sa.bindparam("g", type_=sa.JSON()),
        )
        bind.execute(stmt, {"g": new_graph, "id": workflow_id})


def upgrade() -> None:
    _walk_workflows(_rewrite_graph)

    bind = op.get_bind()
    for old_type, (new_type, _f, _v) in _NODE_TYPE_MAP.items():
        if not old_type.startswith("trigger.meta."):
            continue
        bind.execute(
            sa.text("UPDATE metasubscription SET trigger_type = :new WHERE trigger_type = :old"),
            {"new": new_type, "old": old_type},
        )


def downgrade() -> None:
    _walk_workflows(_downgrade_graph)
    # MetaSubscription.trigger_type can't be reversed without re-reading
    # the workflow graph for each row's event_type — leave consolidated.
