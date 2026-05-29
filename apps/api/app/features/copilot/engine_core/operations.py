"""Apply edit_workflow operations to a workflow graph — partial, validated, with
structured feedback so the LLM self-corrects.

Operations are reordered (delete → add → edit → edge) so forward references in a
single batch resolve. Each op's inputs are validated against the node schema;
valid parts are kept and per-field/per-op errors are collected. Newly added nodes
are auto-positioned; existing nodes keep their layout.

Returns a dict:
    {graph, applied[], input_errors[], skipped[], lint}
"""

from __future__ import annotations

import copy
import uuid
from typing import Any

from apps.api.app.features.copilot.engine_core.layout import layout_new_nodes
from apps.api.app.features.copilot.engine_core.validation import (
    check_required,
    lint_graph,
    validate_node_inputs,
)

# Source-handle names that mean "the node's default output" → stored as no handle.
_DEFAULT_HANDLES = {"", "source", "success", "default", "out"}

# Apply order so a batch can reference nodes it also creates.
_OP_ORDER = {"delete_node": 0, "delete_edge": 1, "add_node": 2, "edit_node": 3, "add_edge": 4}


def _norm_handle(handle: Any) -> str | None:
    if handle is None:
        return None
    h = str(handle)
    return None if h.lower() in _DEFAULT_HANDLES else h


def _edge_id(src: str, tgt: str, handle: str | None) -> str:
    return f"{src}-{handle}-{tgt}" if handle else f"{src}-{tgt}"


def _add_edge(
    edges: list[dict[str, Any]],
    src: str,
    tgt: str,
    source_handle: Any = None,
    target_handle: Any = None,
) -> None:
    sh = _norm_handle(source_handle)
    if any(
        e.get("source") == src and e.get("target") == tgt and e.get("sourceHandle") == sh
        for e in edges
    ):
        return
    edge: dict[str, Any] = {
        "id": _edge_id(src, tgt, sh),
        "source": src,
        "target": tgt,
        "type": "custom",
    }
    if sh:
        edge["sourceHandle"] = sh
    th = _norm_handle(target_handle)
    if th:
        edge["targetHandle"] = th
    edges.append(edge)


def _connection_targets(value: Any) -> list[tuple[str, Any]]:
    """Parse a connections value into [(target_id, target_handle)].
    Accepts: "id" | ["id", ...] | {"block"/"target": id, "handle"?} | list of those."""
    out: list[tuple[str, Any]] = []
    items = value if isinstance(value, list) else [value]
    for item in items:
        if isinstance(item, str):
            out.append((item, None))
        elif isinstance(item, dict):
            tgt = item.get("block") or item.get("target")
            if tgt:
                out.append((str(tgt), item.get("handle") or item.get("targetHandle")))
    return out


def apply_operations(
    graph: dict[str, Any],
    operations: list[dict[str, Any]],
    meta_by_type: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    graph = copy.deepcopy(graph)
    nodes: dict[str, dict[str, Any]] = {n["id"]: n for n in graph.get("nodes", [])}
    pre_ids = set(nodes.keys())
    edges: list[dict[str, Any]] = list(graph.get("edges", []))

    applied: list[dict[str, Any]] = []
    input_errors: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    pending_conn: list[tuple[str, Any, str, Any]] = []  # (src, handle, target, target_handle)

    def _queue_connections(src_id: str, params: dict[str, Any]) -> None:
        for handle, value in (params.get("connections") or {}).items():
            for tgt, th in _connection_targets(value):
                pending_conn.append((src_id, handle, tgt, th))

    ordered = sorted(operations, key=lambda o: _OP_ORDER.get(o.get("type", ""), 99))

    for op in ordered:
        op_type = op.get("type", "")

        if op_type == "add_node":
            node_id = str(op.get("node_id") or uuid.uuid4())
            params = op.get("params") or {}
            ntype = params.get("type", "")
            if not ntype:
                skipped.append(
                    {"op": "add_node", "node_id": node_id, "reason": "missing params.type"}
                )
                continue
            meta = meta_by_type.get(ntype)
            if not meta:
                skipped.append(
                    {"op": "add_node", "node_id": node_id, "reason": f"unknown node type '{ntype}'"}
                )
                continue
            name = params.get("name") or meta.get("name") or ntype
            clean, errs = validate_node_inputs(ntype, params.get("properties") or {}, meta)
            for e in errs:
                e["node_id"] = node_id
            input_errors.extend(errs)
            req = check_required(ntype, clean, meta)
            for e in req:
                e["node_id"] = node_id
            input_errors.extend(req)
            nodes[node_id] = {
                "id": node_id,
                "type": ntype,
                "position": {"x": 0.0, "y": 0.0},
                "data": {"label": name, "properties": clean},
            }
            _queue_connections(node_id, params)
            applied.append({"type": "add_node", "node_id": node_id})

        elif op_type == "edit_node":
            node_id = str(op.get("node_id", ""))
            node = nodes.get(node_id)
            if not node:
                skipped.append({"op": "edit_node", "node_id": node_id, "reason": "node not found"})
                continue
            params = op.get("params") or {}
            ntype = node.get("type", "")
            meta = meta_by_type.get(ntype, {})
            if "name" in params:
                node["data"]["label"] = params["name"]
            if isinstance(params.get("properties"), dict):
                clean, errs = validate_node_inputs(ntype, params["properties"], meta)
                for e in errs:
                    e["node_id"] = node_id
                input_errors.extend(errs)
                node["data"].setdefault("properties", {}).update(clean)
            _queue_connections(node_id, params)
            applied.append({"type": "edit_node", "node_id": node_id})

        elif op_type == "delete_node":
            node_id = str(op.get("node_id", ""))
            if node_id in nodes:
                del nodes[node_id]
                edges = [
                    e for e in edges if e.get("source") != node_id and e.get("target") != node_id
                ]
                applied.append({"type": "delete_node", "node_id": node_id})
            else:
                skipped.append(
                    {"op": "delete_node", "node_id": node_id, "reason": "node not found"}
                )

        elif op_type == "add_edge":
            src = str(op.get("source_id", ""))
            tgt = str(op.get("target_id", ""))
            if src not in nodes:
                skipped.append({"op": "add_edge", "reason": f"source node '{src}' not found"})
                continue
            if tgt not in nodes:
                skipped.append({"op": "add_edge", "reason": f"target node '{tgt}' not found"})
                continue
            _add_edge(edges, src, tgt, op.get("source_handle"), op.get("target_handle"))
            applied.append({"type": "add_edge", "source_id": src, "target_id": tgt})

        elif op_type == "delete_edge":
            src = str(op.get("source_id", ""))
            tgt = str(op.get("target_id", ""))
            edges = [e for e in edges if not (e.get("source") == src and e.get("target") == tgt)]
            applied.append({"type": "delete_edge", "source_id": src, "target_id": tgt})

        else:
            skipped.append({"op": op_type or "(missing)", "reason": "unknown operation type"})

    # Inline connections last, so forward references to just-added nodes resolve.
    for src, handle, tgt, th in pending_conn:
        if src in nodes and tgt in nodes:
            _add_edge(edges, src, tgt, handle, th)
        else:
            missing = src if src not in nodes else tgt
            skipped.append(
                {"op": "connection", "reason": f"connection target '{missing}' not found"}
            )

    node_list = list(nodes.values())
    fixed = pre_ids & set(nodes.keys())
    node_list = layout_new_nodes(node_list, edges, fixed_ids=fixed)
    new_graph = {"nodes": node_list, "edges": edges}

    return {
        "graph": new_graph,
        "applied": applied,
        "input_errors": input_errors,
        "skipped": skipped,
        "lint": lint_graph(new_graph),
    }
