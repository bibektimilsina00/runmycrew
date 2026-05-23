from __future__ import annotations

import copy
import uuid
from typing import Any

from apps.api.app.features.copilot.engine_core.layout import auto_layout


def apply_operations(
    graph: dict[str, Any],
    operations: list[dict[str, Any]],
    known_types: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """
    Apply an ordered list of edit_workflow operations to a workflow graph.

    Returns:
        (updated_graph, errors) — errors is empty on full success.

    Graph format mirrors ReactFlow:
        {
            "nodes": [{"id", "type", "position", "data": {"label", "properties"}}, ...],
            "edges": [{"id", "source", "target", "sourceHandle"?, "targetHandle"?}, ...],
        }
    """
    graph = copy.deepcopy(graph)

    # Index nodes by id for O(1) access
    nodes: dict[str, dict[str, Any]] = {n["id"]: n for n in graph.get("nodes", [])}
    edges: list[dict[str, Any]] = list(graph.get("edges", []))
    errors: list[str] = []

    for op in operations:
        op_type = op.get("type", "")

        # ── add_node ────────────────────────────────────────────────────────
        if op_type == "add_node":
            node_id = str(op.get("node_id") or uuid.uuid4())
            params: dict[str, Any] = op.get("params") or {}
            ntype = params.get("type", "")
            name = params.get("name") or ntype
            properties: dict[str, Any] = params.get("properties") or {}

            if not ntype:
                errors.append("add_node: 'params.type' is required")
                continue
            if ntype not in known_types:
                errors.append(f"add_node: unknown node type '{ntype}'")
                continue

            nodes[node_id] = {
                "id": node_id,
                "type": ntype,
                "position": {"x": 0, "y": 0},
                "data": {"label": name, "properties": properties},
            }

        # ── edit_node ────────────────────────────────────────────────────────
        elif op_type == "edit_node":
            node_id = str(op.get("node_id", ""))
            params = op.get("params") or {}

            if node_id not in nodes:
                errors.append(f"edit_node: node '{node_id}' not found")
                continue

            node = nodes[node_id]
            if "name" in params:
                node["data"]["label"] = params["name"]
            if "properties" in params and isinstance(params["properties"], dict):
                node["data"].setdefault("properties", {}).update(params["properties"])

        # ── delete_node ──────────────────────────────────────────────────────
        elif op_type == "delete_node":
            node_id = str(op.get("node_id", ""))
            if node_id in nodes:
                del nodes[node_id]
                edges = [
                    e for e in edges if e.get("source") != node_id and e.get("target") != node_id
                ]
            else:
                errors.append(f"delete_node: node '{node_id}' not found")

        # ── add_edge ─────────────────────────────────────────────────────────
        elif op_type == "add_edge":
            src = str(op.get("source_id", ""))
            tgt = str(op.get("target_id", ""))

            if src not in nodes:
                errors.append(f"add_edge: source node '{src}' not found")
                continue
            if tgt not in nodes:
                errors.append(f"add_edge: target node '{tgt}' not found")
                continue

            # Skip duplicate edges
            if any(e.get("source") == src and e.get("target") == tgt for e in edges):
                continue

            edge: dict[str, Any] = {"id": f"{src}-{tgt}", "source": src, "target": tgt}
            if op.get("source_handle"):
                edge["sourceHandle"] = op["source_handle"]
            if op.get("target_handle"):
                edge["targetHandle"] = op["target_handle"]
            edges.append(edge)

        # ── delete_edge ──────────────────────────────────────────────────────
        elif op_type == "delete_edge":
            src = str(op.get("source_id", ""))
            tgt = str(op.get("target_id", ""))
            edges = [e for e in edges if not (e.get("source") == src and e.get("target") == tgt)]

        else:
            errors.append(f"Unknown operation type: '{op_type}'")

    node_list = auto_layout(list(nodes.values()), edges)
    return {"nodes": node_list, "edges": edges}, errors
