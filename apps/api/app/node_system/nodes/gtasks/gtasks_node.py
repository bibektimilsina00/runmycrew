"""Google Tasks action node — one node, 12 operations.

Tasklist CRUD
  - `list_tasklists` / `create_tasklist`
  - `rename_tasklist` / `delete_tasklist`

Task CRUD
  - `list_tasks`     / `get_task`
  - `create_task`    / `update_task`
  - `complete_task`  / `delete_task`
  - `move_task`      / `clear_completed`

OAuth scope: `tasks` (already in GoogleOAuthProvider).
"""

from __future__ import annotations

import re
from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

TASKS_API = "https://tasks.googleapis.com/tasks/v1"


_TASK_STATUS_OPTIONS: list[dict[str, str]] = [
    {"label": "Needs action (open)", "value": "needsAction"},
    {"label": "Completed", "value": "completed"},
]


class GoogleTasksProperties(BaseModel):
    credential: str | None = None
    operation: str = "list_tasks"

    # picker (tasklist id) — shared across most ops
    tasklist_id: str | None = None

    # tasklist CRUD
    title: str | None = None
    new_title: str | None = None

    # task fields
    task_id: str | None = None
    task_title: str | None = None
    task_notes: Any = None  # allow expression interpolation
    task_due: str | None = None  # RFC3339 timestamp ("2025-01-01T00:00:00Z")
    task_status: str | None = None  # needsAction / completed
    task_parent: str | None = None  # parent task id (for sub-tasks)

    # list_tasks filters
    show_completed: bool = False
    show_hidden: bool = False
    max_results: int = 100
    due_min: str | None = None
    due_max: str | None = None
    completed_max: str | None = None

    # move_task
    move_parent: str | None = None
    move_previous: str | None = None  # previous-sibling id (positions after this)

    @field_validator("tasklist_id", mode="before")
    @classmethod
    def _coerce_tasklist_id(cls, value: Any) -> str | None:
        # Tasklist picker emits `{id, title}` so the editor can show the
        # name back; runtime only needs the id.
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) and v else None
        if value in (None, ""):
            return None
        return str(value)


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GoogleTasksNode(BaseNode[GoogleTasksProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleTasksProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gtasks",
            name="Google Tasks",
            category="integration",
            description=(
                "Manage Google Tasks via OAuth — tasklists, tasks, "
                "completion, ordering, and bulk clear of finished items."
            ),
            icon="si:SiGoogletasks",
            color="#1a73e8",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "list_tasks",
                    "options": [
                        {"label": "List Tasks", "value": "list_tasks"},
                        {"label": "Get Task", "value": "get_task"},
                        {"label": "Create Task", "value": "create_task"},
                        {"label": "Update Task", "value": "update_task"},
                        {"label": "Mark Task Completed", "value": "complete_task"},
                        {"label": "Delete Task", "value": "delete_task"},
                        {"label": "Move Task (reorder)", "value": "move_task"},
                        {"label": "Clear Completed Tasks", "value": "clear_completed"},
                        {"label": "List Tasklists", "value": "list_tasklists"},
                        {"label": "Create Tasklist", "value": "create_tasklist"},
                        {"label": "Rename Tasklist", "value": "rename_tasklist"},
                        {"label": "Delete Tasklist", "value": "delete_tasklist"},
                    ],
                },
                # tasklist_id picker — required for everything except
                # list_tasklists / create_tasklist
                {
                    "name": "tasklist_id",
                    "label": "Tasklist",
                    "type": "gtasks-tasklist",
                    "required": True,
                    "condition": _cond_any(
                        "list_tasks",
                        "get_task",
                        "create_task",
                        "update_task",
                        "complete_task",
                        "delete_task",
                        "move_task",
                        "clear_completed",
                        "rename_tasklist",
                        "delete_tasklist",
                    ),
                },
                # tasklist CRUD — title fields
                {
                    "name": "title",
                    "label": "Tasklist title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Personal",
                    "condition": _cond("create_tasklist"),
                },
                {
                    "name": "new_title",
                    "label": "New title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Renamed",
                    "condition": _cond("rename_tasklist"),
                },
                # task identity
                {
                    "name": "task_id",
                    "label": "Task ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $trigger.id }}",
                    "condition": _cond_any(
                        "get_task",
                        "update_task",
                        "complete_task",
                        "delete_task",
                        "move_task",
                    ),
                },
                # create_task / update_task — task fields
                {
                    "name": "task_title",
                    "label": "Title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Follow up with client",
                    "condition": _cond("create_task"),
                },
                {
                    "name": "task_title",
                    "label": "Title",
                    "type": "string",
                    "placeholder": "Leave blank to keep current",
                    "condition": _cond("update_task"),
                },
                {
                    "name": "task_notes",
                    "label": "Notes",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 3},
                    "placeholder": "Additional details (optional)",
                    "condition": _cond_any("create_task", "update_task"),
                },
                {
                    "name": "task_due",
                    "label": "Due date",
                    "type": "datetime",
                    "typeOptions": {"granularity": "date"},
                    "description": (
                        "Pick a date or type one. Google Tasks ignores the "
                        "time of day, so we send midnight UTC."
                    ),
                    "condition": _cond_any("create_task", "update_task"),
                },
                {
                    "name": "task_status",
                    "label": "Status",
                    "type": "options",
                    "default": "needsAction",
                    "options": _TASK_STATUS_OPTIONS,
                    "condition": _cond("update_task"),
                    "mode": "advanced",
                },
                {
                    "name": "task_parent",
                    "label": "Parent task ID",
                    "type": "string",
                    "placeholder": "Optional — makes this a sub-task",
                    "condition": _cond("create_task"),
                    "mode": "advanced",
                },
                # list_tasks filters
                {
                    "name": "show_completed",
                    "label": "Include completed",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("list_tasks"),
                },
                {
                    "name": "show_hidden",
                    "label": "Include hidden",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("list_tasks"),
                    "mode": "advanced",
                },
                {
                    "name": "max_results",
                    "label": "Max results",
                    "type": "number",
                    "default": 100,
                    "condition": _cond("list_tasks"),
                    "mode": "advanced",
                },
                {
                    "name": "due_min",
                    "label": "Due after",
                    "type": "datetime",
                    "typeOptions": {"granularity": "datetime"},
                    "condition": _cond("list_tasks"),
                    "mode": "advanced",
                },
                {
                    "name": "due_max",
                    "label": "Due before",
                    "type": "datetime",
                    "typeOptions": {"granularity": "datetime"},
                    "condition": _cond("list_tasks"),
                    "mode": "advanced",
                },
                {
                    "name": "completed_max",
                    "label": "Completed before",
                    "type": "datetime",
                    "typeOptions": {"granularity": "datetime"},
                    "description": "Only meaningful with Include completed on.",
                    "condition": _cond("list_tasks"),
                    "mode": "advanced",
                },
                # move_task
                {
                    "name": "move_parent",
                    "label": "New parent task ID",
                    "type": "string",
                    "placeholder": "Optional — move under this parent",
                    "condition": _cond("move_task"),
                    "mode": "advanced",
                },
                {
                    "name": "move_previous",
                    "label": "Place after task ID",
                    "type": "string",
                    "placeholder": "Optional — previous-sibling id",
                    "description": ("Leave both blank to send the task to the top of the list."),
                    "condition": _cond("move_task"),
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "status", "type": "string"},
                {"label": "due", "type": "string"},
                {"label": "completed", "type": "string"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Google Tasks API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleTasksNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── shared helpers ──────────────────────────────────────────────────────


def _require_tasklist(node: GoogleTasksNode) -> str | NodeResult:
    tlid = (node.props.tasklist_id or "").strip()
    if not tlid:
        return NodeResult(success=False, error="Tasklist is required.")
    return tlid


def _require_task_id(node: GoogleTasksNode) -> str | NodeResult:
    tid = (node.props.task_id or "").strip()
    if not tid:
        return NodeResult(success=False, error="Task ID is required.")
    return tid


_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _normalise_due(value: str) -> str:
    """Coerce date-only input (`YYYY-MM-DD`) to full RFC3339 at midnight
    UTC. The Tasks API rejects bare dates with a 400 even though the
    docs say "only date information is used" — Google parses the field
    strictly first, then drops the time portion.

    Already-RFC3339 strings pass through unchanged.
    """
    if _DATE_ONLY_RE.match(value):
        return f"{value}T00:00:00Z"
    return value


def _build_task_body(node: GoogleTasksNode, *, require_title: bool) -> dict[str, Any] | NodeResult:
    """Shape the JSON body for create_task / update_task. Only fields
    the user actually set get sent — preserves untouched fields on
    update_task."""
    body: dict[str, Any] = {}
    title = (node.props.task_title or "").strip()
    if title:
        body["title"] = title
    elif require_title:
        return NodeResult(success=False, error="Title is required.")
    if node.props.task_notes is not None and str(node.props.task_notes) != "":
        body["notes"] = str(node.props.task_notes)
    due = (node.props.task_due or "").strip()
    if due:
        body["due"] = _normalise_due(due)
    if node.props.task_parent:
        body["parent"] = node.props.task_parent
    if node.props.task_status:
        body["status"] = node.props.task_status
    return body


# ── handlers ────────────────────────────────────────────────────────────


async def _list_tasklists(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    r = await client.get(f"{TASKS_API}/users/@me/lists", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _create_tasklist(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    title = (node.props.title or "").strip()
    if not title:
        return NodeResult(success=False, error="`title` is required.")
    r = await client.post(f"{TASKS_API}/users/@me/lists", headers=headers, json={"title": title})
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _rename_tasklist(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    new_title = (node.props.new_title or "").strip()
    if not new_title:
        return NodeResult(success=False, error="`new_title` is required.")
    r = await client.patch(
        f"{TASKS_API}/users/@me/lists/{tlid}",
        headers=headers,
        json={"title": new_title},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _delete_tasklist(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    r = await client.delete(f"{TASKS_API}/users/@me/lists/{tlid}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data={"tasklist_id": tlid, "deleted": True})


async def _list_tasks(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    params: dict[str, Any] = {
        "showCompleted": "true" if node.props.show_completed else "false",
        "showHidden": "true" if node.props.show_hidden else "false",
        "maxResults": max(1, min(int(node.props.max_results or 100), 100)),
    }
    if node.props.due_min:
        params["dueMin"] = node.props.due_min
    if node.props.due_max:
        params["dueMax"] = node.props.due_max
    if node.props.completed_max:
        params["completedMax"] = node.props.completed_max

    r = await client.get(f"{TASKS_API}/lists/{tlid}/tasks", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_task(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    tid = _require_task_id(node)
    if isinstance(tid, NodeResult):
        return tid
    r = await client.get(f"{TASKS_API}/lists/{tlid}/tasks/{tid}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _create_task(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    body = _build_task_body(node, require_title=True)
    if isinstance(body, NodeResult):
        return body

    # `parent` and `previous` belong as query params, not body, when
    # using POST tasks. Move them across so the API places the task
    # correctly inside the hierarchy.
    params: dict[str, str] = {}
    if node.props.task_parent:
        params["parent"] = node.props.task_parent
        body.pop("parent", None)

    r = await client.post(
        f"{TASKS_API}/lists/{tlid}/tasks",
        headers=headers,
        json=body,
        params=params,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _update_task(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    tid = _require_task_id(node)
    if isinstance(tid, NodeResult):
        return tid
    body = _build_task_body(node, require_title=False)
    if isinstance(body, NodeResult):
        return body
    if not body:
        return NodeResult(success=False, error="Pick at least one field to update.")
    body["id"] = tid  # required by PATCH /tasks/{id}
    r = await client.patch(f"{TASKS_API}/lists/{tlid}/tasks/{tid}", headers=headers, json=body)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _complete_task(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    tid = _require_task_id(node)
    if isinstance(tid, NodeResult):
        return tid
    r = await client.patch(
        f"{TASKS_API}/lists/{tlid}/tasks/{tid}",
        headers=headers,
        json={"id": tid, "status": "completed"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _delete_task(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    tid = _require_task_id(node)
    if isinstance(tid, NodeResult):
        return tid
    r = await client.delete(f"{TASKS_API}/lists/{tlid}/tasks/{tid}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data={"task_id": tid, "deleted": True})


async def _move_task(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    tid = _require_task_id(node)
    if isinstance(tid, NodeResult):
        return tid
    params: dict[str, str] = {}
    if node.props.move_parent:
        params["parent"] = node.props.move_parent
    if node.props.move_previous:
        params["previous"] = node.props.move_previous
    r = await client.post(
        f"{TASKS_API}/lists/{tlid}/tasks/{tid}/move",
        headers=headers,
        params=params,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _clear_completed(
    node: GoogleTasksNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    """Wipes every completed task from the chosen tasklist. Returns 204
    on success — there's no payload, so emit a confirmation dict."""
    tlid = _require_tasklist(node)
    if isinstance(tlid, NodeResult):
        return tlid
    r = await client.post(f"{TASKS_API}/lists/{tlid}/clear", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data={"tasklist_id": tlid, "cleared": True})


_HANDLERS: dict[str, Any] = {
    "list_tasklists": _list_tasklists,
    "create_tasklist": _create_tasklist,
    "rename_tasklist": _rename_tasklist,
    "delete_tasklist": _delete_tasklist,
    "list_tasks": _list_tasks,
    "get_task": _get_task,
    "create_task": _create_task,
    "update_task": _update_task,
    "complete_task": _complete_task,
    "delete_task": _delete_task,
    "move_task": _move_task,
    "clear_completed": _clear_completed,
}
