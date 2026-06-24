from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from apps.api.app.core.logger import get_logger
from apps.api.app.features.copilot.engine_core.node_schema import (
    list_trigger_node_types,
    project_node,
    search_node_types,
)
from apps.api.app.features.copilot.engine_core.operations import apply_operations
from apps.api.app.features.copilot.engine_core.system_prompt import build_system_prompt

logger = get_logger(__name__)

MAX_ITERATIONS = 10

# ── Tool schemas sent to the LLM ─────────────────────────────────────────────
#
# Atomic per-operation tools. Each tool emits a single graph_op SSE event so
# the client can render the workflow building progressively as the model
# emits ops. Replaces the legacy batched `edit_workflow(operations=[...])`
# tool — model-paced streaming is the natural cadence, no artificial sleep.

_ADD_NODE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "add_node",
        "description": (
            "Add ONE node to the workflow. Always call this for every node BEFORE any "
            "`add_edge` that references it. Always fetch the type's schema via "
            "`get_node_metadata` first so `properties` field names are correct."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "Short stable id like 'trigger_1', 'agent_1', 'slack_1'.",
                },
                "type": {
                    "type": "string",
                    "description": "Node type from the index, e.g. 'action.agent', 'trigger.cron'.",
                },
                "name": {
                    "type": "string",
                    "description": "Human-readable label shown on the node card.",
                },
                "properties": {
                    "type": "object",
                    "description": (
                        "Flat {fieldName: value} map matching get_node_metadata. "
                        "Operation-gated fields belong under the chosen operation."
                    ),
                },
            },
            "required": ["node_id", "type"],
        },
    },
}

_UPDATE_NODE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "update_node",
        "description": (
            "Modify an existing node's name and/or properties. Use to fix a property "
            "after the user reports an error, or to wire a placeholder to a real value. "
            "Properties are merged into the existing map (not replaced)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "Existing node id to update."},
                "name": {"type": "string", "description": "New label (optional)."},
                "properties": {
                    "type": "object",
                    "description": "Field updates merged into the node's properties.",
                },
            },
            "required": ["node_id"],
        },
    },
}

_REMOVE_NODE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "remove_node",
        "description": "Delete a node by id. Edges touching it are removed automatically.",
        "parameters": {
            "type": "object",
            "properties": {"node_id": {"type": "string"}},
            "required": ["node_id"],
        },
    },
}

_ADD_EDGE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "add_edge",
        "description": (
            "Connect two nodes. Both must already exist (call `add_node` first). "
            "Use `source_handle` for branch nodes (condition true/false, switch cases)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string"},
                "target_id": {"type": "string"},
                "source_handle": {"type": "string", "description": "Optional. Branch handle name."},
                "target_handle": {"type": "string", "description": "Optional."},
            },
            "required": ["source_id", "target_id"],
        },
    },
}

_REMOVE_EDGE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "remove_edge",
        "description": "Delete an edge between two nodes.",
        "parameters": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string"},
                "target_id": {"type": "string"},
            },
            "required": ["source_id", "target_id"],
        },
    },
}

_SET_WORKFLOW_NAME_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "set_workflow_name",
        "description": (
            "Set the workflow's name. Call this ONCE on first-build of an empty workflow, "
            "or when the user explicitly asks to rename. Skip on follow-up edits."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short Title Case name."},
            },
            "required": ["name"],
        },
    },
}

_GET_NODE_METADATA_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_node_metadata",
        "description": (
            "Get the full field schema (required/optional inputs, per-operation fields, "
            "outputs, credential) for one or more node types. Call this before adding/editing "
            "those node types so you use valid field names."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "node_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Node type IDs — e.g. ['action.agent', 'action.http_request']",
                }
            },
            "required": ["node_types"],
        },
    },
}

_SEARCH_NODE_TYPES_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_node_types",
        "description": (
            "Search the full node catalog by keyword to discover node types not shown in the "
            "index. Returns matching {type, name, description}."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keywords, e.g. 'slack', 'send email'"}
            },
            "required": ["query"],
        },
    },
}

_GET_TRIGGER_NODES_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_trigger_nodes",
        "description": "List node types that can start a workflow (triggers).",
        "parameters": {"type": "object", "properties": {}},
    },
}

_GET_RECENT_RUN_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_recent_run",
        "description": (
            "Get the most recent execution of this workflow: status and per-node error "
            "messages. Use this to diagnose failures before fixing the workflow."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}


# ── SSE helper ────────────────────────────────────────────────────────────────


def _sse(event_type: str, payload: dict[str, Any]) -> str:
    return f"data: {json.dumps({'type': event_type, **payload})}\n\n"


# ── Atomic-op helpers ─────────────────────────────────────────────────────────


def _tool_call_to_op(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Translate one of the atomic tool calls into an `operations.py` op dict.

    Operations.py is the single source of truth for validation, layout and
    edge dedup — atomic tools wrap it with a one-op list so we don't fork
    the rules.
    """
    if tool_name == "add_node":
        return {
            "type": "add_node",
            "node_id": args.get("node_id"),
            "params": {
                "type": args.get("type"),
                "name": args.get("name"),
                "properties": args.get("properties") or {},
            },
        }
    if tool_name == "update_node":
        return {
            "type": "edit_node",
            "node_id": args.get("node_id"),
            "params": {
                "name": args.get("name"),
                "properties": args.get("properties") or {},
            },
        }
    if tool_name == "remove_node":
        return {"type": "delete_node", "node_id": args.get("node_id")}
    if tool_name == "add_edge":
        return {
            "type": "add_edge",
            "source_id": args.get("source_id"),
            "target_id": args.get("target_id"),
            "source_handle": args.get("source_handle"),
            "target_handle": args.get("target_handle"),
        }
    # remove_edge
    return {
        "type": "delete_edge",
        "source_id": args.get("source_id"),
        "target_id": args.get("target_id"),
    }


def _build_op_result(tool_name: str, res: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    """Structured feedback returned to the model after one atomic op."""
    result: dict[str, Any] = {
        "success": bool(res["applied"]),
        "nodes": len(graph.get("nodes", [])),
        "edges": len(graph.get("edges", [])),
    }
    if res["input_errors"]:
        msgs = [f"{e.get('node_id', '?')}.{e['field']}: {e['error']}" for e in res["input_errors"]]
        result["input_validation_message"] = (
            f"{len(msgs)} input(s) rejected (valid inputs were kept): " + "; ".join(msgs)
        )
    if res["skipped"]:
        msgs = [f"{s.get('op')}: {s['reason']}" for s in res["skipped"]]
        result["skipped_message"] = f"{tool_name} skipped: " + "; ".join(msgs)
    return result


def _tool_result_extras(result: dict[str, Any]) -> dict[str, Any]:
    """Subset of result fields safe to leak into the SSE tool_result event."""
    extras: dict[str, Any] = {}
    if "input_validation_message" in result:
        extras["input_validation_message"] = result["input_validation_message"]
    if "skipped_message" in result:
        extras["skipped_message"] = result["skipped_message"]
    return extras


def _graph_op_payload(
    tool_name: str,
    applied: dict[str, Any],
    graph: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    """Build the SSE payload for a single applied op so the client can paint it
    without re-reading the whole graph."""
    op_kind = tool_name  # frontend reducer keys off this
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if tool_name in ("add_node", "update_node"):
        node_id = applied.get("node_id")
        node = next((n for n in nodes if n["id"] == node_id), None)
        return {"op": op_kind, "node_id": node_id, "node": node}

    if tool_name == "remove_node":
        return {"op": op_kind, "node_id": applied.get("node_id")}

    if tool_name == "add_edge":
        src = applied.get("source_id") or args.get("source_id")
        tgt = applied.get("target_id") or args.get("target_id")
        edge = next(
            (e for e in edges if e.get("source") == src and e.get("target") == tgt),
            None,
        )
        return {"op": op_kind, "edge": edge}

    # remove_edge
    return {
        "op": op_kind,
        "source_id": applied.get("source_id"),
        "target_id": applied.get("target_id"),
    }


# ── Main copilot loop ─────────────────────────────────────────────────────────


async def run_copilot(
    *,
    messages: list[dict[str, Any]],
    graph: dict[str, Any],
    workflow_id: str,
    api_key: str,
    ai_api_type: str,
    chat_completions_url: str,
    model: str,
    node_metadata: list[dict[str, Any]],
    db: Any,
    session_id: str | None = None,
    user_id: str = "",
) -> AsyncGenerator[str]:
    """
    Run the Crew AI agentic loop (Sim-style).
    Yields SSE-formatted strings.
    """
    import uuid as _uuid

    from apps.api.app.features.copilot.models import CopilotSession as CopilotSessionModel
    from apps.api.app.features.copilot.repository import CopilotSessionRepository

    meta_by_type = {m["type"]: m for m in node_metadata}
    system_prompt = build_system_prompt(graph, node_metadata)
    current_graph = json.loads(json.dumps(graph))
    graph_dirty = False  # any edit_workflow applied → emit workflow_proposed at the end
    proposed_name: str | None = None  # set by model via edit_workflow.workflow_name

    conversation: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]
    tool_specs = [
        _ADD_NODE_TOOL,
        _UPDATE_NODE_TOOL,
        _REMOVE_NODE_TOOL,
        _ADD_EDGE_TOOL,
        _REMOVE_EDGE_TOOL,
        _SET_WORKFLOW_NAME_TOOL,
        _GET_NODE_METADATA_TOOL,
        _SEARCH_NODE_TYPES_TOOL,
        _GET_TRIGGER_NODES_TOOL,
        _GET_RECENT_RUN_TOOL,
    ]
    all_tool_calls: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for _iter in range(MAX_ITERATIONS):
            content = ""
            tool_calls: list[dict[str, Any]] = []
            # First iteration of every user turn must produce a tool call. Without
            # this, models often return an announcement ("I'll build…") and stop,
            # leaving the editor empty. After iter 0, AUTO lets the model summarize.
            force_tool = _iter == 0
            try:
                if ai_api_type == "openai_compatible":
                    stream = _stream_openai(
                        client,
                        chat_completions_url,
                        api_key,
                        model,
                        conversation,
                        tool_specs,
                        force_tool=force_tool,
                    )
                elif ai_api_type == "anthropic":
                    stream = _stream_anthropic(
                        client,
                        chat_completions_url,
                        api_key,
                        model,
                        conversation,
                        tool_specs,
                        force_tool=force_tool,
                    )
                elif ai_api_type == "google":
                    stream = _stream_google(
                        client,
                        chat_completions_url,
                        api_key,
                        model,
                        conversation,
                        tool_specs,
                        force_tool=force_tool,
                    )
                else:
                    yield _sse("error", {"message": f"Unsupported AI provider type: {ai_api_type}"})
                    return
                async for ev in stream:
                    if ev["type"] == "delta":
                        if ev.get("text"):
                            yield _sse("text_delta", {"content": ev["text"]})
                    elif ev["type"] == "final":
                        content = ev["content"]
                        tool_calls = ev["tool_calls"]
            except httpx.HTTPStatusError as e:
                code = e.response.status_code if e.response is not None else "?"
                yield _sse("error", {"message": f"LLM API error: HTTP {code}"})
                return
            except Exception as e:
                logger.error(f"Copilot LLM call failed (iter {_iter}): {e}", exc_info=True)
                yield _sse("error", {"message": str(e)})
                return

            # No tool calls → conversation complete
            if not tool_calls:
                conversation.append({"role": "assistant", "content": content})
                break

            conversation.append(_build_assistant_msg(content, tool_calls, ai_api_type))

            for tc in tool_calls:
                tool_name = tc["name"]
                args = tc.get("arguments") or {}

                yield _sse("tool_start", {"tool": tool_name})

                # ── Atomic graph ops (one per tool call → one graph_op SSE) ──
                if tool_name in (
                    "add_node",
                    "update_node",
                    "remove_node",
                    "add_edge",
                    "remove_edge",
                ):
                    op = _tool_call_to_op(tool_name, args)
                    res = apply_operations(current_graph, [op], meta_by_type)
                    current_graph = res["graph"]
                    graph_dirty = True
                    applied_now = res["applied"]
                    succeeded = bool(applied_now)
                    result = _build_op_result(tool_name, res, current_graph)

                    # Emit graph_op so the canvas paints THIS op live, before
                    # the model emits the next one. node/edge payload is
                    # post-apply so the client can render without re-reading
                    # the whole graph.
                    if succeeded:
                        yield _sse(
                            "graph_op",
                            _graph_op_payload(tool_name, applied_now[0], current_graph, args),
                        )

                    all_tool_calls.append(
                        {"name": tool_name, "success": succeeded, "result": result}
                    )
                    yield _sse(
                        "tool_result",
                        {"tool": tool_name, "success": succeeded, **_tool_result_extras(result)},
                    )

                elif tool_name == "set_workflow_name":
                    name_arg = args.get("name")
                    if isinstance(name_arg, str) and name_arg.strip():
                        proposed_name = name_arg.strip()
                        result = {"success": True, "name": proposed_name}
                        all_tool_calls.append(
                            {"name": tool_name, "success": True, "result": result}
                        )
                        yield _sse("graph_op", {"op": "set_workflow_name", "name": proposed_name})
                        yield _sse("tool_result", {"tool": tool_name, "success": True})
                    else:
                        result = {"success": False, "error": "name is empty"}
                        all_tool_calls.append(
                            {"name": tool_name, "success": False, "result": result}
                        )
                        yield _sse("tool_result", {"tool": tool_name, "success": False})

                # ── get_node_metadata (batched, compressed projection) ─────
                elif tool_name == "get_node_metadata":
                    requested = args.get("node_types") or (
                        [args["node_type"]] if args.get("node_type") else []
                    )
                    metadata: dict[str, Any] = {}
                    missing: list[str] = []
                    for nt in requested:
                        meta = meta_by_type.get(nt)
                        if meta:
                            metadata[nt] = project_node(meta)
                        else:
                            missing.append(nt)
                    result = {"metadata": metadata}
                    if missing:
                        result["unknown_types"] = missing
                    all_tool_calls.append(
                        {"name": tool_name, "success": bool(metadata), "result": result}
                    )
                    yield _sse("tool_result", {"tool": tool_name, "success": bool(metadata)})

                # ── search_node_types ──────────────────────────────────────
                elif tool_name == "search_node_types":
                    matches = search_node_types(node_metadata, args.get("query", ""))
                    result = {"results": matches}
                    all_tool_calls.append({"name": tool_name, "success": True, "result": result})
                    yield _sse(
                        "tool_result",
                        {"tool": tool_name, "success": True, "count": len(matches)},
                    )

                # ── get_trigger_nodes ──────────────────────────────────────
                elif tool_name == "get_trigger_nodes":
                    result = {"triggers": list_trigger_node_types(node_metadata)}
                    all_tool_calls.append({"name": tool_name, "success": True, "result": result})
                    yield _sse("tool_result", {"tool": tool_name, "success": True})

                # ── get_recent_run (diagnostics for the fix flow) ──────────
                elif tool_name == "get_recent_run":
                    from apps.api.app.features.executions.repository import ExecutionRepository

                    try:
                        exec_repo = ExecutionRepository(db)
                        runs = await exec_repo.list_by_workflow(_uuid.UUID(workflow_id))
                        if not runs:
                            result = {
                                "status": "no_runs",
                                "message": "This workflow has no runs yet.",
                            }
                        else:
                            latest = runs[0]
                            error_logs = await exec_repo.error_logs(latest.id)
                            result = {
                                "status": latest.status,
                                "finished_at": latest.finished_at.isoformat()
                                if latest.finished_at
                                else None,
                                "errors": [
                                    {"node_id": log.node_id, "message": log.message}
                                    for log in error_logs
                                ],
                            }
                    except Exception as e:
                        logger.error(f"get_recent_run failed: {e}", exc_info=True)
                        result = {"error": "Could not load run history."}
                    all_tool_calls.append({"name": tool_name, "success": True, "result": result})
                    yield _sse("tool_result", {"tool": tool_name, "success": True})

                else:
                    result = {"error": f"Unknown tool: '{tool_name}'"}
                    all_tool_calls.append({"name": tool_name, "success": False, "result": result})
                    yield _sse("tool_result", {"tool": tool_name, "success": False})

                conversation.append(_build_tool_result_msg(tc, result, ai_api_type))

    # ── Propose changes (no DB write — client diffs + Accept persists) ──────────
    if graph_dirty:
        payload: dict[str, Any] = {"graph": current_graph}
        if proposed_name:
            payload["name"] = proposed_name
        yield _sse("workflow_proposed", payload)

    # ── Save session ──────────────────────────────────────────────────────────
    if user_id and workflow_id:
        # Build storable messages (user + assistant, skip system/tool messages)
        storable: list[dict[str, Any]] = []
        for m in conversation:
            role = m.get("role", "")
            if role == "user":
                content_val = m.get("content", "")
                if isinstance(content_val, str) and content_val:
                    storable.append({"role": "user", "content": content_val})
            elif role == "assistant":
                content_val = m.get("content") or ""
                if isinstance(content_val, str):
                    storable.append({"role": "assistant", "content": content_val})

        # If the model only called tools and produced no text, add a summary message
        successful_tools = [tc for tc in all_tool_calls if tc["success"]]
        if not any(m["role"] == "assistant" and m.get("content") for m in storable):
            if successful_tools:
                fallback = f"Done — {len(successful_tools)} tool{'s' if len(successful_tools) > 1 else ''} executed successfully."
            elif all_tool_calls:
                fallback = "Tool execution failed."
            else:
                fallback = ""
            if fallback:
                storable.append({"role": "assistant", "content": fallback})

        # Generate title from first user message
        title = "New Chat"
        for m in storable:
            if m["role"] == "user" and m["content"]:
                title = m["content"][:60].strip()
                if len(m["content"]) > 60:
                    title += "..."
                break

        # Attach tool call metadata to last assistant message
        visible_tool_calls = [
            {"tool": tc["name"], "success": tc["success"]}
            for tc in all_tool_calls
            if not str(tc.get("result", {}).get("error", "")).startswith("Duplicate")
        ]
        if storable and storable[-1]["role"] == "assistant" and visible_tool_calls:
            storable[-1]["tool_calls"] = visible_tool_calls

        # Save to DB
        session_repo = CopilotSessionRepository(db)
        saved_session_id = session_id
        try:
            if session_id:
                existing = await session_repo.get_by_id_and_user(
                    _uuid.UUID(session_id), _uuid.UUID(user_id)
                )
                if existing:
                    await session_repo.update(existing, {"messages": storable, "title": title})
                else:
                    session_id = None  # fall through to create

            if not session_id:
                new_session = CopilotSessionModel(
                    workflow_id=_uuid.UUID(workflow_id),
                    user_id=_uuid.UUID(user_id),
                    title=title,
                    messages=storable,
                )
                created = await session_repo.create(new_session)
                saved_session_id = str(created.id)

            yield _sse("session_saved", {"session_id": saved_session_id, "title": title})
        except Exception as _se:
            logger.error(f"Failed to save copilot session: {_se}", exc_info=True)

    yield _sse("done", {})


# ── LLM callers ───────────────────────────────────────────────────────────────


async def _stream_openai(
    client: httpx.AsyncClient,
    url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    tool_specs: list[dict[str, Any]],
    force_tool: bool = False,
) -> AsyncGenerator[dict[str, Any]]:
    payload: dict[str, Any] = {"model": model, "messages": messages, "stream": True}
    if tool_specs:
        payload["tools"] = tool_specs
        payload["tool_choice"] = "required" if force_tool else "auto"
    content = ""
    acc: dict[int, dict[str, str]] = {}  # index -> {id, name, args(str)}
    async with client.stream(
        "POST",
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
    ) as resp:
        if resp.status_code >= 400:
            await resp.aread()
            resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data or data == "[DONE]":
                continue
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            text = delta.get("content")
            if text:
                content += text
                yield {"type": "delta", "text": text}
            for tcd in delta.get("tool_calls") or []:
                slot = acc.setdefault(tcd.get("index", 0), {"id": "", "name": "", "args": ""})
                if tcd.get("id"):
                    slot["id"] = tcd["id"]
                fn = tcd.get("function") or {}
                if fn.get("name"):
                    slot["name"] += fn["name"]
                if fn.get("arguments"):
                    slot["args"] += fn["arguments"]
    yield {"type": "final", "content": content, "tool_calls": _finalize_openai_calls(acc)}


def _finalize_openai_calls(acc: dict[int, dict[str, str]]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for idx in sorted(acc):
        slot = acc[idx]
        try:
            args = json.loads(slot["args"]) if slot["args"].strip() else {}
        except json.JSONDecodeError:
            args = {}
        calls.append({"id": slot["id"] or f"call_{idx}", "name": slot["name"], "arguments": args})
    return calls


async def _stream_anthropic(
    client: httpx.AsyncClient,
    url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    tool_specs: list[dict[str, Any]],
    force_tool: bool = False,
) -> AsyncGenerator[dict[str, Any]]:
    system_msgs = [m["content"] for m in messages if m.get("role") == "system"]
    chat_msgs = [
        {
            "role": "assistant" if m.get("role") == "assistant" else "user",
            "content": m.get("content", ""),
        }
        for m in messages
        if m.get("role") != "system"
    ]
    payload: dict[str, Any] = {
        "model": model,
        # Match the Gemini path: multi-node edit_workflow calls can blow past
        # a 4k cap and truncate mid-tool-use (leaving the user with no graph).
        "max_tokens": 16384,
        "messages": chat_msgs,
        "stream": True,
    }
    if system_msgs:
        payload["system"] = "\n\n".join(system_msgs)
    if tool_specs:
        payload["tools"] = [_to_anthropic_tool(t) for t in tool_specs]
        payload["tool_choice"] = {"type": "any"} if force_tool else {"type": "auto"}
    content = ""
    blocks: dict[int, dict[str, Any]] = {}  # index -> {type, id, name, text, json}
    async with client.stream(
        "POST",
        url,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json=payload,
    ) as resp:
        if resp.status_code >= 400:
            await resp.aread()
            resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data:
                continue
            try:
                ev = json.loads(data)
            except json.JSONDecodeError:
                continue
            etype = ev.get("type")
            if etype == "content_block_start":
                cb = ev.get("content_block") or {}
                blocks[ev.get("index", 0)] = {
                    "type": cb.get("type"),
                    "id": cb.get("id", ""),
                    "name": cb.get("name", ""),
                    "text": "",
                    "json": "",
                }
            elif etype == "content_block_delta":
                slot = blocks.setdefault(
                    ev.get("index", 0), {"type": "text", "text": "", "json": ""}
                )
                delta = ev.get("delta") or {}
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        slot["text"] += text
                        content += text
                        yield {"type": "delta", "text": text}
                elif delta.get("type") == "input_json_delta":
                    slot["json"] += delta.get("partial_json", "")
    tool_calls: list[dict[str, Any]] = []
    for idx in sorted(blocks):
        b = blocks[idx]
        if b.get("type") == "tool_use":
            try:
                args = json.loads(b["json"]) if b["json"].strip() else {}
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(
                {"id": b.get("id") or f"toolu_{idx}", "name": b.get("name", ""), "arguments": args}
            )
    yield {"type": "final", "content": content, "tool_calls": tool_calls}


async def _stream_google(
    client: httpx.AsyncClient,
    url_template: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    tool_specs: list[dict[str, Any]],
    force_tool: bool = False,
) -> AsyncGenerator[dict[str, Any]]:
    system_msgs = [m["content"] for m in messages if m.get("role") == "system"]
    contents: list[dict[str, Any]] = []
    for m in messages:
        role_in = m.get("role")
        if role_in == "system":
            continue
        # Messages built by _build_assistant_msg / _build_tool_result_msg for Google
        # already carry the Gemini shape: role ∈ {"model","user"} + "parts".
        if "parts" in m:
            contents.append({"role": role_in or "user", "parts": m["parts"]})
            continue
        role = "model" if role_in == "assistant" else "user"
        content_val = m.get("content", "")
        if isinstance(content_val, list):
            contents.append({"role": role, "parts": content_val})
        else:
            contents.append({"role": role, "parts": [{"text": str(content_val)}]})

    payload: dict[str, Any] = {
        "contents": contents,
        # A single edit_workflow call easily exceeds the default ~2k output
        # token cap for a multi-node workflow (each node's properties + edges
        # are emitted inline). Raising this prevents the model from truncating
        # mid-tool-call, which manifests as "text-only" iterations that leave
        # the user with no workflow.
        "generationConfig": {"maxOutputTokens": 16384},
    }
    if system_msgs:
        payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_msgs)}]}
    if tool_specs:
        payload["tools"] = [{"functionDeclarations": [_to_google_tool(t) for t in tool_specs]}]
        if force_tool:
            payload["toolConfig"] = {"functionCallingConfig": {"mode": "ANY"}}

    model_path = model.removeprefix("models/")
    url = url_template.format(model=model_path)
    if ":generateContent" in url:
        url = url.replace(":generateContent", ":streamGenerateContent")

    content = ""
    tool_calls: list[dict[str, Any]] = []
    async with client.stream(
        "POST",
        url,
        params={"key": api_key, "alt": "sse"},
        headers={"Content-Type": "application/json"},
        json=payload,
    ) as resp:
        if resp.status_code >= 400:
            await resp.aread()
            resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data:
                continue
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            candidates = chunk.get("candidates") or []
            parts = (candidates[0].get("content") or {}).get("parts", []) if candidates else []
            for part in parts:
                if not isinstance(part, dict):
                    continue
                if part.get("text"):
                    content += part["text"]
                    yield {"type": "delta", "text": part["text"]}
                if "functionCall" in part:
                    call = part["functionCall"]
                    tool_calls.append(
                        {
                            "id": call.get("name", ""),
                            "name": call.get("name", ""),
                            "arguments": call.get("args") or {},
                        }
                    )
    yield {"type": "final", "content": content, "tool_calls": tool_calls}


# ── Message builders ──────────────────────────────────────────────────────────


def _build_assistant_msg(
    content: str,
    tool_calls: list[dict[str, Any]],
    api_type: str,
) -> dict[str, Any]:
    if api_type == "anthropic":
        blocks: list[dict[str, Any]] = []
        if content:
            blocks.append({"type": "text", "text": content})
        for tc in tool_calls:
            blocks.append(
                {
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc.get("arguments") or {},
                }
            )
        return {"role": "assistant", "content": blocks}

    if api_type == "google":
        gparts: list[dict[str, Any]] = []
        if content:
            gparts.append({"text": content})
        for tc in tool_calls:
            gparts.append({"functionCall": {"name": tc["name"], "args": tc.get("arguments") or {}}})
        return {"role": "model", "parts": gparts}  # type: ignore[return-value]

    # OpenAI-compatible
    return {
        "role": "assistant",
        "content": content or None,
        "tool_calls": [
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": json.dumps(tc.get("arguments") or {}),
                },
            }
            for tc in tool_calls
        ],
    }


def _build_tool_result_msg(
    tc: dict[str, Any],
    result: Any,
    api_type: str,
) -> dict[str, Any]:
    result_text = json.dumps(result)

    if api_type == "anthropic":
        return {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tc["id"], "content": result_text}],
        }

    if api_type == "google":
        resp = result if isinstance(result, dict) else {"result": result_text}
        return {
            "role": "user",
            "parts": [{"functionResponse": {"name": tc["name"], "response": resp}}],
        }

    return {"role": "tool", "tool_call_id": tc["id"], "content": result_text}


# ── Tool format converters ────────────────────────────────────────────────────


def _to_anthropic_tool(openai_spec: dict[str, Any]) -> dict[str, Any]:
    fn = (
        openai_spec.get("function")
        if isinstance(openai_spec.get("function"), dict)
        else openai_spec
    )
    return {
        "name": fn.get("name", ""),
        "description": fn.get("description", ""),
        "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
    }


def _to_google_tool(openai_spec: dict[str, Any]) -> dict[str, Any]:
    fn = (
        openai_spec.get("function")
        if isinstance(openai_spec.get("function"), dict)
        else openai_spec
    )
    params = fn.get("parameters") or {"type": "object", "properties": {}}
    # Google doesn't support additionalProperties or default — strip them
    params = _clean_for_google(params)
    return {
        "name": fn.get("name", ""),
        "description": fn.get("description", ""),
        "parameters": params,
    }


def _clean_for_google(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively remove keys Google's API rejects (additionalProperties, default)."""
    cleaned: dict[str, Any] = {}
    for k, v in schema.items():
        if k in ("additionalProperties", "default"):
            continue
        if isinstance(v, dict):
            cleaned[k] = _clean_for_google(v)
        elif k == "properties" and isinstance(v, dict):
            cleaned[k] = {
                pk: _clean_for_google(pv) if isinstance(pv, dict) else pv for pk, pv in v.items()
            }
        elif k == "items" and isinstance(v, dict):
            cleaned[k] = _clean_for_google(v)
        else:
            cleaned[k] = v
    return cleaned
