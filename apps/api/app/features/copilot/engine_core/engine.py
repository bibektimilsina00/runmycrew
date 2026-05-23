from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from apps.api.app.core.logger import get_logger
from apps.api.app.features.copilot.engine_core.operations import apply_operations
from apps.api.app.features.copilot.engine_core.system_prompt import build_system_prompt

logger = get_logger(__name__)

MAX_ITERATIONS = 10

# ── Tool schemas sent to the LLM ─────────────────────────────────────────────

_EDIT_WORKFLOW_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "edit_workflow",
        "description": (
            "Create or modify the workflow by applying a list of operations atomically. "
            "Always batch all operations for a single logical change into one call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operations": {
                    "type": "array",
                    "description": "Ordered list of edit operations",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "add_node",
                                    "edit_node",
                                    "delete_node",
                                    "add_edge",
                                    "delete_edge",
                                ],
                                "description": "Operation type",
                            },
                            "node_id": {
                                "type": "string",
                                "description": "Node ID. For add_node: desired ID. For edit/delete_node: existing ID.",
                            },
                            "source_id": {
                                "type": "string",
                                "description": "Source node ID (add_edge / delete_edge)",
                            },
                            "target_id": {
                                "type": "string",
                                "description": "Target node ID (add_edge / delete_edge)",
                            },
                            "source_handle": {
                                "type": "string",
                                "description": "Source handle (optional)",
                            },
                            "target_handle": {
                                "type": "string",
                                "description": "Target handle (optional)",
                            },
                            "params": {
                                "type": "object",
                                "description": (
                                    "add_node: {type, name, properties}. "
                                    "edit_node: {name?, properties?}."
                                ),
                            },
                        },
                        "required": ["type"],
                    },
                }
            },
            "required": ["operations"],
        },
    },
}

_GET_NODE_METADATA_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_node_metadata",
        "description": "Get the full metadata (all properties and their types) for a specific node type.",
        "parameters": {
            "type": "object",
            "properties": {
                "node_type": {
                    "type": "string",
                    "description": "Node type ID — e.g. 'action.agent', 'action.http_request'",
                }
            },
            "required": ["node_type"],
        },
    },
}


# ── SSE helper ────────────────────────────────────────────────────────────────


def _sse(event_type: str, payload: dict[str, Any]) -> str:
    return f"data: {json.dumps({'type': event_type, **payload})}\n\n"


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
    Run the Fuse Copilot agentic loop (Sim-style).
    Yields SSE-formatted strings.
    """
    import uuid as _uuid

    from apps.api.app.features.copilot.models import CopilotSession as CopilotSessionModel
    from apps.api.app.features.copilot.repository import CopilotSessionRepository
    from apps.api.app.features.workflows.repository import WorkflowRepository

    known_types = {m["type"] for m in node_metadata}
    system_prompt = build_system_prompt(graph, node_metadata)
    current_graph = json.loads(json.dumps(graph))

    conversation: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]
    tool_specs = [_EDIT_WORKFLOW_TOOL, _GET_NODE_METADATA_TOOL]
    all_tool_calls: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for _iter in range(MAX_ITERATIONS):
            try:
                if ai_api_type == "openai_compatible":
                    raw = await _call_openai(
                        client, chat_completions_url, api_key, model, conversation, tool_specs
                    )
                    content, tool_calls = _extract_openai(raw)
                elif ai_api_type == "anthropic":
                    raw = await _call_anthropic(
                        client, chat_completions_url, api_key, model, conversation, tool_specs
                    )
                    content, tool_calls = _extract_anthropic(raw)
                elif ai_api_type == "google":
                    raw = await _call_google(
                        client, chat_completions_url, api_key, model, conversation, tool_specs
                    )
                    content, tool_calls = _extract_google(raw)
                else:
                    yield _sse("error", {"message": f"Unsupported AI provider type: {ai_api_type}"})
                    return
            except httpx.HTTPStatusError as e:
                yield _sse("error", {"message": f"LLM API error: HTTP {e.response.status_code}"})
                return
            except Exception as e:
                logger.error(f"Copilot LLM call failed (iter {_iter}): {e}", exc_info=True)
                yield _sse("error", {"message": str(e)})
                return

            # Emit text content to client
            if content:
                yield _sse("text_delta", {"content": content})

            # No tool calls → conversation complete
            if not tool_calls:
                conversation.append({"role": "assistant", "content": content})
                break

            conversation.append(_build_assistant_msg(content, tool_calls, ai_api_type))

            for tc in tool_calls:
                tool_name = tc["name"]
                args = tc.get("arguments") or {}

                yield _sse("tool_start", {"tool": tool_name})

                # ── edit_workflow ─────────────────────────────────────────
                if tool_name == "edit_workflow":
                    operations: list[dict[str, Any]] = args.get("operations", [])
                    updated_graph, errors = apply_operations(current_graph, operations, known_types)

                    if errors:
                        result: dict[str, Any] = {"success": False, "errors": errors}
                        all_tool_calls.append(
                            {"name": tool_name, "success": False, "result": {"error": str(errors)}}
                        )
                        yield _sse(
                            "tool_result", {"tool": tool_name, "success": False, "errors": errors}
                        )
                    else:
                        current_graph = updated_graph

                        # Persist updated graph to DB
                        try:
                            repo = WorkflowRepository(db)
                            wf = await repo.get_by_id(uuid.UUID(workflow_id))
                            if wf:
                                await repo.update(wf, {"graph": current_graph})
                        except Exception as e:
                            logger.error(f"Failed to persist graph: {e}", exc_info=True)

                        result = {
                            "success": True,
                            "nodes": len(current_graph.get("nodes", [])),
                            "edges": len(current_graph.get("edges", [])),
                        }
                        all_tool_calls.append(
                            {"name": tool_name, "success": True, "result": result}
                        )
                        yield _sse("tool_result", {"tool": tool_name, "success": True})
                        yield _sse("workflow_updated", {"graph": current_graph})

                # ── get_node_metadata ─────────────────────────────────────
                elif tool_name == "get_node_metadata":
                    node_type = args.get("node_type", "")
                    meta = next((m for m in node_metadata if m["type"] == node_type), None)
                    result = meta if meta else {"error": f"Node type '{node_type}' not found"}
                    all_tool_calls.append(
                        {"name": tool_name, "success": meta is not None, "result": result}
                    )
                    yield _sse("tool_result", {"tool": tool_name, "success": meta is not None})

                else:
                    result = {"error": f"Unknown tool: '{tool_name}'"}
                    all_tool_calls.append({"name": tool_name, "success": False, "result": result})
                    yield _sse("tool_result", {"tool": tool_name, "success": False})

                conversation.append(_build_tool_result_msg(tc, result, ai_api_type))

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


async def _call_openai(
    client: httpx.AsyncClient,
    url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    tool_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": model, "messages": messages}
    if tool_specs:
        payload["tools"] = tool_specs
        payload["tool_choice"] = "auto"
    resp = await client.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


async def _call_anthropic(
    client: httpx.AsyncClient,
    url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    tool_specs: list[dict[str, Any]],
) -> dict[str, Any]:
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
        "max_tokens": 4096,
        "messages": chat_msgs,
    }
    if system_msgs:
        payload["system"] = "\n\n".join(system_msgs)
    if tool_specs:
        payload["tools"] = [_to_anthropic_tool(t) for t in tool_specs]
        payload["tool_choice"] = {"type": "auto"}
    resp = await client.post(
        url,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


async def _call_google(
    client: httpx.AsyncClient,
    url_template: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    tool_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    system_msgs = [m["content"] for m in messages if m.get("role") == "system"]
    contents: list[dict[str, Any]] = []
    for m in messages:
        if m.get("role") == "system":
            continue
        role = "model" if m.get("role") == "assistant" else "user"
        # Handle content that's already in Google parts format
        content = m.get("content", "")
        if isinstance(content, list):
            contents.append({"role": role, "parts": content})
        else:
            contents.append({"role": role, "parts": [{"text": str(content)}]})

    payload: dict[str, Any] = {"contents": contents}
    if system_msgs:
        payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_msgs)}]}
    if tool_specs:
        payload["tools"] = [{"functionDeclarations": [_to_google_tool(t) for t in tool_specs]}]

    model_path = model.removeprefix("models/")
    url = url_template.format(model=model_path)
    resp = await client.post(
        url,
        params={"key": api_key},
        headers={"Content-Type": "application/json"},
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


# ── Response extractors ───────────────────────────────────────────────────────


def _extract_openai(raw: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    choices = raw.get("choices") or []
    message = (choices[0] if choices else {}).get("message") or {}
    content = str(message.get("content") or "")
    tool_calls: list[dict[str, Any]] = []
    for tc in message.get("tool_calls") or []:
        fn = tc.get("function") or {}
        try:
            args = json.loads(fn.get("arguments", "{}"))
        except json.JSONDecodeError:
            args = {}
        tool_calls.append({"id": tc.get("id", ""), "name": fn.get("name", ""), "arguments": args})
    return content, tool_calls


def _extract_anthropic(raw: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    blocks = raw.get("content") or []
    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif block.get("type") == "tool_use":
            tool_calls.append(
                {
                    "id": block.get("id", ""),
                    "name": block.get("name", ""),
                    "arguments": block.get("input") or {},
                }
            )
    return "".join(text_parts), tool_calls


def _extract_google(raw: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    candidates = raw.get("candidates") or []
    parts = (candidates[0] if candidates else {}).get("content", {}).get("parts", [])
    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if "text" in part:
            text_parts.append(part["text"])
        if "functionCall" in part:
            call = part["functionCall"]
            tool_calls.append(
                {
                    "id": call.get("name", ""),
                    "name": call.get("name", ""),
                    "arguments": call.get("args") or {},
                }
            )
    return "".join(text_parts), tool_calls


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
