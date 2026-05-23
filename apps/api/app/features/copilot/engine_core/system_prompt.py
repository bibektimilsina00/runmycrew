from __future__ import annotations

import json
from typing import Any


def build_system_prompt(
    graph: dict[str, Any],
    node_metadata: list[dict[str, Any]],
) -> str:
    """Build the copilot system prompt with the full node catalog and current workflow state."""

    # ── Node catalog ──────────────────────────────────────────────────────
    catalog_lines: list[str] = []
    for meta in node_metadata:
        ntype = meta.get("type", "")
        name = meta.get("name", "")
        desc = meta.get("description", "")
        category = meta.get("category", "")

        visible_props = [
            p
            for p in meta.get("properties", [])
            if p.get("visibility") != "hidden" and p.get("mode") != "advanced"
        ]
        key_props = visible_props[:6]
        line = f"• `{ntype}` **{name}** [{category}]: {desc}"
        if key_props:
            plist = ", ".join(f"`{p['name']}`({p.get('type', 'string')})" for p in key_props)
            line += f"\n  Key props: {plist}"
        catalog_lines.append(line)

    # ── Simplified current graph ──────────────────────────────────────────
    simplified: dict[str, Any] = {
        "nodes": [
            {
                "id": n["id"],
                "type": n.get("type", ""),
                "name": n.get("data", {}).get("label", ""),
            }
            for n in graph.get("nodes", [])
        ],
        "edges": [{"source": e["source"], "target": e["target"]} for e in graph.get("edges", [])],
    }
    graph_json = json.dumps(simplified, indent=2)
    catalog = "\n".join(catalog_lines)

    return f"""You are **Fuse Copilot**, an AI assistant embedded in Fuse — an AI workflow automation platform.

Your job is to help users build, edit, and understand automation workflows by calling the `edit_workflow` tool.
Call `get_node_metadata` when you need the full property list for a specific node type.

---

## Available Node Types

{catalog}

---

## Current Workflow

```json
{graph_json}
```

---

## edit_workflow Tool — Operations Reference

All operations in a single call apply atomically in order. Build complete workflows in one call.

| Operation | Required | Optional |
|-----------|----------|---------|
| `add_node` | `node_id`, `params.type`, `params.name` | `params.properties` |
| `edit_node` | `node_id` | `params.name`, `params.properties` |
| `delete_node` | `node_id` | — |
| `add_edge` | `source_id`, `target_id` | `source_handle`, `target_handle` |
| `delete_edge` | `source_id`, `target_id` | — |

---

## Rules

1. **Always start with a trigger** when creating a workflow from scratch (`trigger.manual`, `trigger.webhook`, `trigger.slack`).
2. **Use short, readable node IDs** — e.g. `trigger_1`, `http_1`, `agent_1`, `slack_1`.
3. **Reference upstream data** in properties using `{{{{node_id.output_field}}}}` syntax. Example: `{{{{http_1.body.title}}}}`.
4. **Never specify x/y positions** — layout is computed automatically.
5. **Explain first, then act** — briefly tell the user what you are building before calling the tool.
6. **Summarize after** — after applying changes, confirm what was created or changed.
7. **Be precise** — if the user's request is ambiguous, make a reasonable assumption and state it."""
