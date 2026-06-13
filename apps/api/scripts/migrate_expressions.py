"""One-shot rewrite: every legacy `{{...}}` template → JSONata `=…`.

Covers all six legacy namespaces in one pass:
- `{{nodeId.output.path}}` / `{{nodeId.path}}` → `=$node('Label').path`
- `{{trigger.output.path}}` / `{{trigger.path}}` → `=$trigger.path`
- `{{variables.path}}` → `=$vars.path`
- `{{env.NAME}}` → `=$env.NAME`
- `{{secrets.NAME}}` → `=$secrets.NAME`
- `{{loop.path}}` → `=$loop.path`

Only single-template strings are migrated — mixed-text values like
`"Hello {{x.y}}"` or `"{{a.x}}{{b.y}}"` need JSONata string-concat to
become safe and are out of scope; the legacy resolver continues to
serve those until they're rewritten by hand.

Run **before** deploying the follow-up that deletes TemplateResolver.
Idempotent — re-running is a no-op because rewritten strings start
with `=`.

Usage:
    python -m apps.api.scripts.migrate_expressions [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import re
from typing import Any

from sqlalchemy import select

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.core.logger import get_logger
from apps.api.app.features.workflows.models import Workflow

logger = get_logger(__name__)


# Matches `{{<head>...}}` and captures the inner. `[^}]+` is loose on purpose:
# the legacy resolver itself only handles single `{{ }}` pairs without nesting.
LEGACY_TEMPLATE = re.compile(r"\{\{([^}]+)\}\}")

# Each legacy namespace and its JSONata replacement variable name. Keys are
# the saved `{{<head>.…}}` head; values are the binding name we use in
# JsonataResolver (`variables` → `$vars` matches the existing binding label).
NAMESPACE_VARS: dict[str, str] = {
    "trigger": "trigger",
    "variables": "vars",
    "env": "env",
    "secrets": "secrets",
    "loop": "loop",
}


def _safe_label_for_call(label: str) -> str:
    """Escape a label so it sits inside `$node('...')` safely."""
    return label.replace("\\", "\\\\").replace("'", "\\'")


def _split_node_path(inner: str, id_to_label: dict[str, str]) -> tuple[str, str] | None:
    """Match the inner of a `{{...}}` template against the node-id namespace.

    Returns ``(label, remaining_path)`` when the template refers to a known
    node id; ``None`` otherwise so the caller leaves the template alone.

    Handles two legacy forms seen in production graphs:
    - ``nodeId.output.foo.bar`` — explicit `.output` marker
    - ``nodeId.foo.bar``        — implicit (resolver fell back to context lookup)

    The node id itself may contain dots (e.g. ``action.http_request-123``),
    so we don't split on `.` blindly. Instead we try every prefix from
    longest to shortest against the id table.
    """
    inner = inner.strip()
    head = inner.split(".", 1)[0]
    if head in NAMESPACE_VARS:
        return None

    # Longest-first match — handles ids containing dots.
    candidate_ids = sorted(id_to_label.keys(), key=len, reverse=True)
    for nid in candidate_ids:
        if inner == nid:
            return id_to_label[nid], ""
        if inner.startswith(f"{nid}."):
            remainder = inner[len(nid) + 1 :]
            remainder = remainder.removeprefix("output.")
            if remainder == "output":
                remainder = ""
            return id_to_label[nid], remainder
    return None


def _split_namespace_path(inner: str) -> tuple[str, str] | None:
    """Match the inner against the workflow-wide namespaces.

    Returns ``(jsonata_var, remainder)`` where ``jsonata_var`` is the
    binding name (e.g. ``trigger`` for ``$trigger``) and ``remainder`` is
    the dot-path under it. ``{{trigger.output.x}}`` and ``{{trigger.x}}``
    both collapse to ``("trigger", "x")`` because the legacy resolver
    stripped the implicit ``.output`` segment too.
    """
    inner = inner.strip()
    head, _, rest = inner.partition(".")
    var = NAMESPACE_VARS.get(head)
    if var is None:
        return None
    # Only the trigger namespace had an `.output` sub-layer in the legacy
    # data shape; strip it so the migrated expression doesn't carry a
    # dead segment.
    if var == "trigger":
        rest = rest.removeprefix("output.")
        if rest == "output":
            rest = ""
    return var, rest


def _rewrite_string(source: str, id_to_label: dict[str, str]) -> tuple[str, int]:
    """Migrate one string. Returns ``(new_source, changes)``.

    Only **single-template** strings — where the entire value is exactly
    one `{{...}}` reference to a known node — are rewritten to the
    JSONata `=$node('Label').path` form. Mixed-text strings (`"Hello
    {{x.y}}"`) and multi-template strings are left to the legacy
    resolver; touching them would require building a JSONata string
    concat, which is out of scope here.
    """
    if not isinstance(source, str):
        return source, 0
    if source.startswith("="):
        # Already JSONata. Idempotent skip.
        return source, 0

    stripped = source.strip()
    if not (stripped.startswith("{{") and stripped.endswith("}}")):
        return source, 0
    if stripped.count("{{") != 1 or stripped.count("}}") != 1:
        # Multi-template — defer to legacy resolver for now.
        return source, 0

    inner = stripped[2:-2].strip()

    # Workflow-wide namespaces (`trigger`, `vars`, `env`, `secrets`, `loop`)
    # take priority — their names cannot collide with node ids because the
    # node-id lookup explicitly bails on these heads.
    ns_parsed = _split_namespace_path(inner)
    if ns_parsed is not None:
        var, remainder = ns_parsed
        new_source = f"=${var}.{remainder}" if remainder else f"=${var}"
        return new_source, 1

    node_parsed = _split_node_path(inner, id_to_label)
    if node_parsed is None:
        return source, 0

    label, remainder = node_parsed
    call = f"$node('{_safe_label_for_call(label)}')"
    new_source = f"={call}.{remainder}" if remainder else f"={call}"
    return new_source, 1


def _rewrite_value(value: Any, id_to_label: dict[str, str]) -> tuple[Any, int]:
    """Walk a property value (dict / list / string / primitive)."""
    if isinstance(value, str):
        return _rewrite_string(value, id_to_label)
    if isinstance(value, list):
        changes = 0
        out: list[Any] = []
        for item in value:
            rewritten, c = _rewrite_value(item, id_to_label)
            out.append(rewritten)
            changes += c
        return out, changes
    if isinstance(value, dict):
        changes = 0
        out_dict: dict[str, Any] = {}
        for k, v in value.items():
            rewritten, c = _rewrite_value(v, id_to_label)
            out_dict[k] = rewritten
            changes += c
        return out_dict, changes
    return value, 0


def migrate_graph(graph: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Rewrite every property string in a graph's nodes. Returns (new_graph, changes).

    Builds the id→label snapshot from the graph's nodes at the moment of
    the call, so the migration uses whatever label the user has at this
    instant — not labels from a different point in time.
    """
    nodes = graph.get("nodes", [])
    id_to_label: dict[str, str] = {}
    for node in nodes:
        nid = node.get("id")
        if not nid:
            continue
        label = (node.get("data") or {}).get("label") or nid
        id_to_label[nid] = label

    total_changes = 0
    new_nodes: list[dict[str, Any]] = []
    for node in nodes:
        data = node.get("data") or {}
        properties = data.get("properties") or {}
        new_props, changes = _rewrite_value(properties, id_to_label)
        total_changes += changes
        if changes:
            new_data = {**data, "properties": new_props}
            new_nodes.append({**node, "data": new_data})
        else:
            new_nodes.append(node)

    if total_changes == 0:
        return graph, 0
    return {**graph, "nodes": new_nodes}, total_changes


async def _run(dry_run: bool) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Workflow))
        workflows = result.scalars().all()
        logger.info("Scanning %d workflow(s) for legacy expressions…", len(workflows))

        total_changes = 0
        touched = 0
        for wf in workflows:
            new_graph, changes = migrate_graph(wf.graph)
            if changes == 0:
                continue
            logger.info("Workflow %s (%s): %d expression(s) rewritten", wf.id, wf.name, changes)
            total_changes += changes
            touched += 1
            if not dry_run:
                wf.graph = new_graph
                session.add(wf)

        if not dry_run:
            await session.commit()
        suffix = " (dry run, no commit)" if dry_run else ""
        logger.info(
            "Done%s — %d workflow(s) modified, %d expression(s) rewritten.",
            suffix,
            touched,
            total_changes,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report counts without writing anything back.",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.dry_run))


if __name__ == "__main__":
    main()
