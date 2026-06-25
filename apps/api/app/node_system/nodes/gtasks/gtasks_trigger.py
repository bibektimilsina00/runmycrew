"""Google Tasks trigger node — polling-driven task-event detection.

Two event types, distinct cursor shapes:

  - `task_added` — fires once per task added to the chosen tasklist.
      cursor: ``{event_type: "task_added", known_ids: [id, id, …]}``
      First poll snapshots the set of currently-existing task ids and
      emits nothing; later polls emit one match per id absent from the
      cursor's set.

  - `task_completed` — fires once per task transitioning to status
    "completed".
      cursor: ``{event_type: "task_completed", completion: {id: bool}}``
      First poll snapshots the per-task completion state and emits
      nothing; later polls emit on every false→true transition.

A cursor whose `event_type` doesn't match the node's current setting
is treated as a first poll (resnapshots cleanly when the user swaps
between the two events).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.repository import IntegrationTriggerStateRepository
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

TASKS_API = "https://tasks.googleapis.com/tasks/v1"
PROVIDER = "google_tasks"
DEFAULT_POLL_INTERVAL_SECONDS = 60

EVENT_TASK_ADDED = "task_added"
EVENT_TASK_COMPLETED = "task_completed"
EVENT_TYPES = (EVENT_TASK_ADDED, EVENT_TASK_COMPLETED)


class GoogleTasksTriggerProperties(BaseModel):
    credential: str | None = None
    event_type: str = EVENT_TASK_ADDED
    tasklist_id: str = ""
    # Cap fan-out per poll so a backlog spike (e.g. after downtime)
    # doesn't dispatch hundreds of executions at once.
    max_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    @field_validator("tasklist_id", mode="before")
    @classmethod
    def _coerce_tasklist_id(cls, value: Any) -> str:
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) else ""
        return str(value) if value is not None else ""

    @field_validator("event_type", mode="before")
    @classmethod
    def _coerce_event_type(cls, value: Any) -> str:
        v = str(value or "").strip().lower()
        return v if v in EVENT_TYPES else EVENT_TASK_ADDED


class GoogleTasksTriggerNode(BaseNode[GoogleTasksTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleTasksTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gtasks_change",
            name="Google Tasks",
            category="trigger",
            description=(
                "Fires when tasks are added to or completed inside the picked "
                "tasklist. First poll snapshots silently; later polls emit one "
                "execution per matching task."
            ),
            icon="google-tasks",
            color="#1c1c1c",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": EVENT_TASK_ADDED,
                    "options": [
                        {"label": "Task added", "value": EVENT_TASK_ADDED},
                        {"label": "Task completed", "value": EVENT_TASK_COMPLETED},
                    ],
                },
                {
                    "name": "tasklist_id",
                    "label": "Tasklist",
                    "type": "gtasks-tasklist",
                    "required": True,
                },
                {
                    "name": "max_per_poll",
                    "label": "Max events per poll",
                    "type": "number",
                    "default": 25,
                    "mode": "advanced",
                },
                {
                    "name": "poll_interval_seconds",
                    "label": "Poll interval (seconds)",
                    "type": "number",
                    "default": DEFAULT_POLL_INTERVAL_SECONDS,
                    "mode": "advanced",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "status", "type": "string"},
                {"label": "due", "type": "string"},
                {"label": "completed", "type": "string"},
                {"label": "tasklist_id", "type": "string"},
                {"label": "event_type", "type": "string"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Scheduler-dispatched payload — pass through.
        if (
            isinstance(input_data, dict)
            and input_data.get("id")
            and input_data.get("event_type") in EVENT_TYPES
        ):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")
        if not self.props.tasklist_id:
            return NodeResult(success=False, error="Tasklist is required.")

        workflow_id = getattr(context, "workflow_id", None)
        node_id = getattr(context, "node_id", None)
        workspace_id = getattr(context, "workspace_id", None)
        db = getattr(context, "db", None)
        wf_uuid = _safe_uuid(workflow_id)
        ws_uuid = _safe_uuid(workspace_id)
        if wf_uuid is None or ws_uuid is None or db is None or not node_id:
            return await self._stateless_preview(token)

        repo = IntegrationTriggerStateRepository(db)
        state = await repo.get(wf_uuid, node_id)
        cursor = state.cursor if state else None

        try:
            matches, new_cursor = await self.poll(token, cursor)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Google Tasks API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("GoogleTasksTriggerNode poll failed: %s", exc, exc_info=True)
            return NodeResult(success=False, error=str(exc))

        await repo.upsert(
            workflow_id=wf_uuid,
            workspace_id=ws_uuid,
            node_id=node_id,
            provider=PROVIDER,
            cursor=new_cursor,
            next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
            last_error=None,
        )
        await db.commit()

        if not matches:
            return NodeResult(
                success=True,
                output_data={"matched": 0, "tasks": [], **_cursor_summary(new_cursor)},
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=matches[0])

    # ── public poll API ────────────────────────────────────────────────

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        tlid = self.props.tasklist_id
        event_type = self.props.event_type
        # Cursor from a different event_type → first poll for new event.
        prior_event = (cursor or {}).get("event_type")
        if cursor and prior_event != event_type:
            cursor = None

        async with httpx.AsyncClient(timeout=30) as client:
            tasks = await _fetch_tasks(client, headers, tlid)

        if event_type == EVENT_TASK_COMPLETED:
            return self._diff_task_completed(tasks, cursor, tlid)
        return self._diff_task_added(tasks, cursor, tlid)

    # ── per-event diff functions ───────────────────────────────────────

    def _diff_task_added(
        self,
        tasks: list[dict[str, Any]],
        cursor: dict[str, Any] | None,
        tlid: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        current_ids = [str(t.get("id")) for t in tasks if t.get("id")]
        prior_ids = (cursor or {}).get("known_ids")

        # First poll → snapshot only.
        if not isinstance(prior_ids, list):
            return [], {"event_type": EVENT_TASK_ADDED, "known_ids": current_ids}

        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        emitted_ids: set[str] = set()
        for t in tasks:
            tid = str(t.get("id") or "")
            if not tid or tid in known:
                continue
            matches.append(_normalize(t, tlid, EVENT_TASK_ADDED))
            emitted_ids.add(tid)
            if len(matches) >= max_per_poll:
                break
        # Persist emitted + previously-known. Un-emitted new ids stay
        # absent from `known_ids` so the next tick re-considers them.
        next_known = list(known | emitted_ids)
        return matches, {"event_type": EVENT_TASK_ADDED, "known_ids": next_known}

    def _diff_task_completed(
        self,
        tasks: list[dict[str, Any]],
        cursor: dict[str, Any] | None,
        tlid: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        # Cursor stores `{id: completed?}` per task. The list call
        # includes both open + completed when we ask for them; we
        # always pass `showCompleted=true` in `_fetch_tasks` so we see
        # transitions.
        now_state: dict[str, bool] = {
            str(t.get("id")): str(t.get("status") or "") == "completed"
            for t in tasks
            if t.get("id")
        }
        prior = (cursor or {}).get("completion")
        if not isinstance(prior, dict):
            return [], {"event_type": EVENT_TASK_COMPLETED, "completion": now_state}

        matches: list[dict[str, Any]] = []
        emitted_ids: set[str] = set()
        for t in tasks:
            tid = str(t.get("id") or "")
            if not tid:
                continue
            was = bool(prior.get(tid, False))
            now = now_state.get(tid, False)
            if not was and now:
                matches.append(_normalize(t, tlid, EVENT_TASK_COMPLETED))
                emitted_ids.add(tid)
                if len(matches) >= max_per_poll:
                    break

        # Persist emitted transitions. Un-emitted (still-open or
        # not-yet-emitted completions) keep their prior state so the
        # next tick still sees them as needing a transition.
        next_state = dict(prior)
        for tid, is_complete in now_state.items():
            if tid in emitted_ids:
                next_state[tid] = is_complete
            elif tid not in prior:
                # Newly-seen open task — record so we won't fire on it
                # later if it was actually already complete at first
                # sight (matches the "first poll snapshot" semantics).
                next_state[tid] = is_complete
        return matches, {"event_type": EVENT_TASK_COMPLETED, "completion": next_state}

    async def _stateless_preview(self, token: str) -> NodeResult:
        """Preview / listen path with no DB context — return the most
        recent task in the list as a one-shot preview match."""
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            tasks = await _fetch_tasks(client, headers, self.props.tasklist_id)
        if not tasks:
            return NodeResult(
                success=True,
                output_data={
                    "matched": 0,
                    "tasks": [],
                    "event_type": self.props.event_type,
                },
                handled_successors=True,
            )
        latest = tasks[0]
        return NodeResult(
            success=True,
            output_data=_normalize(latest, self.props.tasklist_id, self.props.event_type),
        )


# ── helpers ─────────────────────────────────────────────────────────────


async def _fetch_tasks(
    client: httpx.AsyncClient, headers: dict[str, str], tasklist_id: str
) -> list[dict[str, Any]]:
    """Pull every task — both open and completed — so the diff can spot
    transitions either direction."""
    r = await client.get(
        f"{TASKS_API}/lists/{tasklist_id}/tasks",
        headers=headers,
        params={
            "showCompleted": "true",
            "showHidden": "true",
            "maxResults": 100,
        },
    )
    r.raise_for_status()
    return list(r.json().get("items") or [])


def _normalize(task: dict[str, Any], tasklist_id: str, event_type: str) -> dict[str, Any]:
    return {
        "id": task.get("id"),
        "title": task.get("title") or "",
        "status": task.get("status") or "",
        "due": task.get("due") or "",
        "completed": task.get("completed") or "",
        "notes": task.get("notes") or "",
        "parent": task.get("parent") or "",
        "position": task.get("position") or "",
        "tasklist_id": tasklist_id,
        "event_type": event_type,
        "payload": task,
    }


def _safe_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _next_poll_at(interval_seconds: int) -> datetime:
    seconds = max(30, min(int(interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS), 60 * 60))
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _cursor_summary(cursor: dict[str, Any]) -> dict[str, Any]:
    """Slim the persisted cursor for output — full id list / completion
    map would balloon execution logs on every empty poll."""
    event = cursor.get("event_type") or EVENT_TASK_ADDED
    if event == EVENT_TASK_COMPLETED:
        completion = cursor.get("completion") or {}
        return {"event_type": event, "tracked_tasks": len(completion)}
    return {"event_type": event, "known_tasks": len(cursor.get("known_ids") or [])}


# ── scheduler integration ──────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    node = GoogleTasksTriggerNode.__new__(GoogleTasksTriggerNode)
    node.props = GoogleTasksTriggerProperties(
        credential=None,
        event_type=str(props.get("event_type") or EVENT_TASK_ADDED),
        tasklist_id=props.get("tasklist_id") or "",
        max_per_poll=int(props.get("max_per_poll") or 25),
        poll_interval_seconds=int(
            props.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS
        ),
    )
    return await node.poll(token, cursor)


def _register() -> None:
    try:
        from apps.api.app.execution_engine.scheduler.integration_polling import (
            register_poller,
        )
    except Exception:  # noqa: BLE001
        return
    register_poller(
        node_type="trigger.gtasks_change",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()
