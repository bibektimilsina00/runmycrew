from __future__ import annotations

from typing import Any


def auto_layout(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Assign x/y positions to nodes using a left-to-right DAG layout (Kahn BFS levels).
    Called after every edit_workflow operation so the AI never needs to specify coordinates.
    """
    if not nodes:
        return nodes

    H_SPACING = 300
    V_SPACING = 130
    START_X = 100
    START_Y = 300

    node_ids = {n["id"] for n in nodes}

    children: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    parents: dict[str, list[str]] = {n["id"]: [] for n in nodes}

    for edge in edges:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src in node_ids and tgt in node_ids:
            children[src].append(tgt)
            parents[tgt].append(src)

    # Kahn's BFS — assign column (depth) to each node
    in_degree = {n["id"]: len(parents[n["id"]]) for n in nodes}
    queue: list[str] = [n["id"] for n in nodes if in_degree[n["id"]] == 0]
    column: dict[str, int] = {}
    col = 0

    while queue:
        next_queue: list[str] = []
        for nid in queue:
            if nid not in column:
                column[nid] = col
            for child in children[nid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_queue.append(child)
        queue = next_queue
        col += 1

    # Assign disconnected / cycle nodes to the last column
    for n in nodes:
        if n["id"] not in column:
            column[n["id"]] = col

    # Group nodes by column, then assign rows
    cols: dict[int, list[str]] = {}
    for nid, c in column.items():
        cols.setdefault(c, []).append(nid)

    positions: dict[str, dict[str, float]] = {}
    for c, nids in cols.items():
        x = START_X + c * H_SPACING
        total_h = (len(nids) - 1) * V_SPACING
        for row, nid in enumerate(nids):
            y = START_Y + row * V_SPACING - total_h / 2
            positions[nid] = {"x": float(x), "y": float(y)}

    for node in nodes:
        if node["id"] in positions:
            node["position"] = positions[node["id"]]

    return nodes
