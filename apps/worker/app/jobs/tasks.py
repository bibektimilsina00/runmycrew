from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from apps.api.app.core.celery import celery_app
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="execute_workflow")
def execute_workflow(
    execution_id: str,
    workflow_id: str,
    graph: dict,
    trigger_data: dict,
    resume_from: str | None = None,
    resume_input: dict | None = None,
    snapshot: dict | None = None,
):
    """Main workflow execution task. Handles both fresh runs and resumes."""
    try:
        asyncio.run(
            _run_workflow(
                execution_id,
                workflow_id,
                graph,
                trigger_data,
                resume_from=resume_from,
                resume_input=resume_input,
                snapshot=snapshot,
            )
        )
    except Exception as e:
        logger.error(f"execute_workflow task failed: {e}", exc_info=True)


async def _run_workflow(
    execution_id: str,
    workflow_id: str,
    graph: dict,
    trigger_data: dict,
    resume_from: str | None = None,
    resume_input: dict | None = None,
    snapshot: dict | None = None,
):
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.execution_engine.engine.event_emitter import RedisEventEmitter
    from apps.api.app.execution_engine.engine.workflow_runner import (
        CancelledException,
        PauseSignal,
        WorkflowRunner,
    )
    from apps.api.app.features.credentials.service import CredentialService
    from apps.api.app.features.executions.repository import ExecutionRepository
    from apps.api.app.features.workflows.repository import WorkflowRepository

    credentials_list: list[dict[str, Any]] = []
    secrets_dict: dict[str, str] = {}
    workspace_id_str: str | None = None
    workflow_name = workflow_id

    async with AsyncSessionLocal() as db:
        wf_repo = WorkflowRepository(db)
        workflow = await wf_repo.get_by_id(uuid.UUID(workflow_id))
        if workflow:
            workspace_id_str = str(workflow.workspace_id)
            workflow_name = workflow.name
            credential_service = CredentialService(db)
            credentials_list = await credential_service.list_decrypted_for_user(workflow.user_id)
            # Load user secrets for {{secrets.KEY}} interpolation
            try:
                import sqlalchemy as sa

                from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
                from apps.api.app.features.secrets.models import Secret

                _enc = AESEncryptionService()
                result = await db.execute(
                    sa.select(Secret).where(Secret.user_id == workflow.user_id)
                )
                from contextlib import suppress

                for s in result.scalars().all():
                    with suppress(Exception):
                        secrets_dict[s.name] = _enc.decrypt(s.encrypted_value)
            except Exception as e:
                logger.warning(f"Failed to load secrets for workflow {workflow_id}: {e}")
        else:
            logger.error(f"Workflow {workflow_id} not found when fetching credentials")

    emitter = RedisEventEmitter(execution_id, workspace_id=workspace_id_str)

    async def log_and_emit(
        message: str, level: str = "info", node_id: str | None = None, payload: Any = None
    ) -> None:
        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            log = await repo.add_log(
                uuid.UUID(execution_id), message, level=level, node_id=node_id, payload=payload
            )
        # Use the DB-stored timestamp so live + catch-up events carry the
        # exact same timestamp string (catch-up reads `log.timestamp`).
        ts = log.timestamp.isoformat()
        if not ts.endswith("Z") and "+00:00" not in ts:
            ts += "Z"
        await emitter.emit(
            "log_synced",
            {
                "type": "log_synced",
                # Stable DB id so the frontend dedupes live + catch-up events.
                "id": str(log.id),
                "node_id": node_id,
                "lvl": "err" if level == "error" else ("warn" if level == "warn" else "info"),
                "src": workflow_name,
                "msg": message,
                "payload": payload,
                "t": ts,
                "timestamp": ts,
            },
        )

    async with AsyncSessionLocal() as db:
        exec_repo = ExecutionRepository(db)
        await exec_repo.update_status(uuid.UUID(execution_id), "running")

    await log_and_emit("Workflow execution started", level="info")
    await emitter.emit("execution_started", {})

    try:
        async with AsyncSessionLocal() as db:
            runner = WorkflowRunner(
                workflow_id=workflow_id,
                execution_id=execution_id,
                graph=graph,
                db=db,
                on_log=log_and_emit,
                credentials=credentials_list,
                emitter=emitter,
                workspace_id=workspace_id_str,
            )
            if workflow:
                runner.env = workflow.env or {}
                runner.secrets = secrets_dict

            # If resuming, restore snapshot state so already-run nodes are skipped
            if resume_from and snapshot:
                runner._executed = {nid: True for nid in snapshot.get("executed_nodes", [])}
                runner._outputs = snapshot.get("node_outputs", {})
                runner.variables = snapshot.get("variables", {})
                # Resume from the paused node with human input
                output = await runner._resume_from(resume_from, resume_input or {})
            else:
                output = await runner.run(trigger_data)

        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            await repo.update_status(uuid.UUID(execution_id), "completed", output_data=output)

        await log_and_emit("Workflow execution completed", level="info")
        await emitter.emit("execution_completed", {"status": "completed", "output": output})

    except CancelledException:
        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            await repo.update_status(uuid.UUID(execution_id), "cancelled")

        await log_and_emit("Execution cancelled by user", level="warn")
        await emitter.emit("execution_cancelled", {"status": "cancelled"})
        logger.info(f"Execution {execution_id} cancelled")

    except PauseSignal as pause:
        import secrets

        token = secrets.token_urlsafe(32)
        snap = {
            "executed_nodes": list(runner._executed.keys()),
            "node_outputs": runner._outputs,
            "variables": runner.variables,
            "graph": graph,  # store so resume endpoint can re-enqueue
        }
        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            await repo.save_pause(
                uuid.UUID(execution_id),
                node_id=pause.node_id,
                resume_token=token,
                resume_schema=pause.resume_schema,
                snapshot=snap,
            )
        await emitter.emit(
            "execution_paused",
            {
                "node_id": pause.node_id,
                "resume_token": token,
                "resume_schema": pause.resume_schema,
            },
        )
        logger.info(f"Execution {execution_id} paused at node {pause.node_id}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Workflow {workflow_id} failed: {error_msg}")
        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            await repo.update_status(uuid.UUID(execution_id), "failed")

        await log_and_emit(error_msg, level="error")
        await emitter.emit("execution_failed", {"status": "failed", "error": error_msg})
        raise


@celery_app.task(name="execute_crew")
def execute_crew(
    crew_execution_id: str,
    crew_id: str,
    graph: dict,
    trigger_data: dict,
):
    """Crew execution task. Reuses WorkflowRunner via _run_crew."""
    try:
        asyncio.run(
            _run_crew(
                crew_execution_id,
                crew_id,
                graph,
                trigger_data,
            )
        )
    except Exception as e:
        logger.error(f"execute_crew task failed: {e}", exc_info=True)


async def _run_crew(
    crew_execution_id: str,
    crew_id: str,
    graph: dict,
    trigger_data: dict,
):
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.execution_engine.engine.event_emitter import RedisEventEmitter
    from apps.api.app.execution_engine.engine.workflow_runner import (
        CancelledException,
        PauseSignal,
        WorkflowRunner,
    )
    from apps.api.app.features.credentials.service import CredentialService
    from apps.api.app.features.crews.models import Crew
    from apps.api.app.features.crews.repository import CrewExecutionRepository

    credentials_list: list[dict[str, Any]] = []
    secrets_dict: dict[str, str] = {}
    workspace_id_str: str | None = None
    crew_env: dict[str, Any] = {}

    async with AsyncSessionLocal() as db:
        crew = await db.get(Crew, uuid.UUID(crew_id))
        if crew:
            workspace_id_str = str(crew.workspace_id)
            credential_service = CredentialService(db)
            credentials_list = await credential_service.list_decrypted_for_user(crew.user_id)
            # Load user secrets for {{secrets.KEY}} interpolation
            try:
                import sqlalchemy as sa

                from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
                from apps.api.app.features.secrets.models import Secret

                _enc = AESEncryptionService()
                result = await db.execute(sa.select(Secret).where(Secret.user_id == crew.user_id))
                from contextlib import suppress

                for s in result.scalars().all():
                    with suppress(Exception):
                        secrets_dict[s.name] = _enc.decrypt(s.encrypted_value)
            except Exception as e:
                logger.warning(f"Failed to load secrets for crew {crew_id}: {e}")
        else:
            logger.error(f"Crew {crew_id} not found when fetching credentials")

    emitter = RedisEventEmitter(crew_execution_id, workspace_id=workspace_id_str)

    async with AsyncSessionLocal() as db:
        repo = CrewExecutionRepository(db)
        await repo.update_status(uuid.UUID(crew_execution_id), "running")

    await emitter.emit("execution_started", {})

    try:
        async with AsyncSessionLocal() as db:
            # crew_id is passed as WorkflowRunner's workflow_id; the runner's
            # concurrency mutex falls back to "skip" when no Workflow row exists.
            runner = WorkflowRunner(
                workflow_id=crew_id,
                execution_id=crew_execution_id,
                graph=graph,
                db=db,
                credentials=credentials_list,
                emitter=emitter,
                workspace_id=workspace_id_str,
            )
            runner.env = crew_env
            runner.secrets = secrets_dict
            # Seed the crew-level cost gate. AgentNode reads these from
            # context.variables to stop firing once the cap is hit.
            if crew is not None and (crew.max_cost_usd or 0) > 0:
                runner.variables["_crew_cost_cap"] = float(crew.max_cost_usd)
                runner.variables["_crew_cost_used"] = 0.0

            output = await runner.run(trigger_data)

        async with AsyncSessionLocal() as db:
            repo = CrewExecutionRepository(db)
            await repo.update_status(uuid.UUID(crew_execution_id), "completed", output_data=output)

        await emitter.emit("execution_completed", {"status": "completed", "output": output})

    except CancelledException:
        async with AsyncSessionLocal() as db:
            repo = CrewExecutionRepository(db)
            await repo.update_status(uuid.UUID(crew_execution_id), "cancelled")

        await emitter.emit("execution_cancelled", {"status": "cancelled"})
        logger.info(f"Crew execution {crew_execution_id} cancelled")

    except PauseSignal as pause:
        import secrets

        token = secrets.token_urlsafe(32)
        snap = {
            "executed_nodes": list(runner._executed.keys()),
            "node_outputs": runner._outputs,
            "variables": runner.variables,
            "graph": graph,
        }
        async with AsyncSessionLocal() as db:
            repo = CrewExecutionRepository(db)
            await repo.save_pause(
                uuid.UUID(crew_execution_id),
                node_id=pause.node_id,
                resume_token=token,
                resume_schema=pause.resume_schema,
                snapshot=snap,
            )
        await emitter.emit(
            "execution_paused",
            {
                "node_id": pause.node_id,
                "resume_token": token,
                "resume_schema": pause.resume_schema,
            },
        )
        logger.info(f"Crew execution {crew_execution_id} paused at node {pause.node_id}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Crew {crew_id} failed: {error_msg}")
        async with AsyncSessionLocal() as db:
            repo = CrewExecutionRepository(db)
            await repo.update_status(uuid.UUID(crew_execution_id), "failed")

        await emitter.emit("execution_failed", {"status": "failed", "error": error_msg})
        raise


@celery_app.task(name="execute_app_message")
def execute_app_message(
    execution_id: str,
    workflow_id: str | None,
    session_id: str,
    assistant_message_id: str,
    user_message: str,
    form_data: dict | None = None,
    crew_id: str | None = None,
):
    """Run one turn of a chat-app workflow.

    Loads the workflow's current graph (no snapshot — always live),
    injects the visitor's message + session history as the trigger
    payload, streams events over the Redis pub/sub channel the SSE
    endpoint subscribes to, then persists the final reply + artifacts
    on the AppMessage placeholder.
    """
    try:
        asyncio.run(
            _run_app_message(
                execution_id,
                workflow_id,
                session_id,
                assistant_message_id,
                user_message,
                form_data or {},
                crew_id,
            )
        )
    except Exception as e:
        logger.error(f"execute_app_message task failed: {e}", exc_info=True)
        # The visitor is watching an SSE stream and a spinner. A silent
        # crash here left the placeholder empty forever — persist the
        # failure and emit a terminal event so the page can say so.
        try:
            asyncio.run(_fail_app_message(execution_id, assistant_message_id, str(e)))
        except Exception:
            logger.error("could not persist app-message failure", exc_info=True)


async def _fail_app_message(execution_id: str, assistant_message_id: str, error: str) -> None:
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.execution_engine.engine.event_emitter import RedisEventEmitter
    from apps.api.app.features.apps.repository import AppMessageRepository

    async with AsyncSessionLocal() as db:
        repo = AppMessageRepository(db)
        msg = await repo.get_by_id(uuid.UUID(assistant_message_id))
        if msg and not msg.content:
            await repo.update(msg, {"content": f"Something went wrong: {error}", "is_error": True})
    emitter = RedisEventEmitter(execution_id)
    await emitter.emit("execution_failed", {"status": "failed", "error": error})


async def _run_app_message(
    execution_id: str,
    workflow_id: str | None,
    session_id: str,
    assistant_message_id: str,
    user_message: str,
    form_data: dict,
    crew_id: str | None = None,
):
    import time

    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.execution_engine.engine.event_emitter import RedisEventEmitter
    from apps.api.app.execution_engine.engine.workflow_runner import (
        CancelledException,
        WorkflowRunner,
    )
    from apps.api.app.features.apps.repository import (
        AppMessageRepository,
        AppSessionRepository,
    )
    from apps.api.app.features.credentials.service import CredentialService
    from apps.api.app.features.workflows.repository import WorkflowRepository

    started_at = time.time()

    workspace_id_str: str | None = None
    credentials_list: list[dict[str, Any]] = []
    graph: dict[str, Any] = {}
    history_messages: list[dict[str, Any]] = []
    allow_history = True
    persona_id: str | None = None
    user_id_for_run: uuid.UUID | None = None

    async with AsyncSessionLocal() as db:
        session_repo = AppSessionRepository(db)
        message_repo = AppMessageRepository(db)
        # The chat-app source is a workflow OR a crew — same graph shape,
        # same runner; only the row it's loaded from differs.
        if crew_id:
            from apps.api.app.features.crews.models import Crew

            workflow = await db.get(Crew, uuid.UUID(crew_id))
        else:
            wf_repo = WorkflowRepository(db)
            workflow = await wf_repo.get_by_id(uuid.UUID(workflow_id))
        if not workflow:
            logger.error(f"chat-app source {crew_id or workflow_id} not found")
            return
        session = await session_repo.get_by_id(uuid.UUID(session_id))
        if not session:
            logger.error(f"app session {session_id} not found")
            return
        workspace_id_str = str(workflow.workspace_id)
        graph = workflow.graph or {"nodes": [], "edges": []}
        # Chat-app config lives on the trigger.chat_app node's data.properties.
        trigger_props: dict[str, Any] = {}
        for node in graph.get("nodes") or []:
            if isinstance(node, dict) and node.get("type") == "trigger.chat_app":
                trigger_props = (node.get("data") or {}).get("properties") or {}
                break
        allow_history = bool(trigger_props.get("allow_history", True))
        persona_id = trigger_props.get("system_persona_id")
        user_id_for_run = workflow.user_id  # runs charge against workflow owner

        if allow_history:
            prior = await message_repo.list_by_session(session.id, limit=20)
            for m in prior:
                if m.role in ("user", "assistant") and m.content:
                    history_messages.append({"role": m.role, "content": m.content})

        credential_service = CredentialService(db)
        credentials_list = await credential_service.list_decrypted_for_user(user_id_for_run)

    emitter = RedisEventEmitter(execution_id, workspace_id=workspace_id_str)
    await emitter.emit("execution_started", {"kind": "app_message"})

    trigger_data = {
        "message": user_message,
        "session_id": session_id,
        "user_id": None,
        "files": [],
        "form_data": form_data,
        "history": history_messages,
    }

    final_output: dict[str, Any] = {}
    collected_artifacts: list[dict] = []
    node_statuses: dict[str, str] = {}
    error_msg: str | None = None
    tokens = 0
    cost_usd = 0.0

    try:
        async with AsyncSessionLocal() as db:
            runner = WorkflowRunner(
                workflow_id=workflow_id,
                execution_id=execution_id,
                graph=graph,
                db=db,
                credentials=credentials_list,
                emitter=emitter,
                workspace_id=workspace_id_str,
            )
            # Persona overlay for the first agent node in the graph.
            if persona_id:
                runner.variables["_persona_overlay_id"] = persona_id
            try:
                final_output = await runner.run(trigger_data) or {}
            finally:
                # Final per-node lifecycle — retained for late WS
                # subscribers (fast runs finish before the editor's
                # socket lands, and pub/sub has no replay).
                node_statuses = {
                    nid: ("completed" if getattr(res, "success", False) else "failed")
                    for nid, res in runner._executed.items()
                }
            # Pull the runner's accumulated artifacts BEFORE the session
            # closes — after we exit the async-with the runner is dead.
            collected_artifacts = [
                a.model_dump() if hasattr(a, "model_dump") else a
                for a in runner._collected_artifacts
            ]

        # Aggregate usage from any agent_usage snapshots the runner produced.
        for value in _walk_dict(final_output):
            if isinstance(value, dict) and "total_cost_usd" in value:
                cost_usd += float(value.get("total_cost_usd") or 0.0)
            if isinstance(value, dict) and "total_input_tokens" in value:
                tokens += int(value.get("total_input_tokens") or 0) + int(
                    value.get("total_output_tokens") or 0
                )

        terminal_event = ("execution_completed", {"status": "completed", "output": final_output})
    except CancelledException:
        error_msg = "Cancelled"
        terminal_event = ("execution_cancelled", {"status": "cancelled"})
    except Exception as e:
        error_msg = str(e)
        logger.error(f"app-message execution {execution_id} failed: {error_msg}")
        terminal_event = ("execution_failed", {"status": "failed", "error": error_msg})

    # Ride the final per-node lifecycle on the terminal event: sockets that
    # subscribed mid-run missed the individual node_* frames, and the
    # terminal is the one event every subscriber is guaranteed to see
    # (live via pub/sub, or replayed from the retained snapshot).
    terminal_event[1]["node_statuses"] = node_statuses

    latency_ms = int((time.time() - started_at) * 1000)
    reply_text, inline_artifacts = _extract_reply(final_output)
    # Merge: any artifacts a node explicitly returned in its output_data
    # (rare) come last so runner-collected ones (which include auto-detected
    # + node-attached) win the id de-dup.
    seen_ids: set[str] = set()
    artifacts: list[dict] = []
    for a in collected_artifacts + inline_artifacts:
        aid = a.get("id") if isinstance(a, dict) else None
        if aid and aid in seen_ids:
            continue
        if aid:
            seen_ids.add(aid)
        artifacts.append(a)

    async with AsyncSessionLocal() as db:
        message_repo = AppMessageRepository(db)
        session_repo = AppSessionRepository(db)
        msg = await message_repo.get_by_id(uuid.UUID(assistant_message_id))
        if msg:
            await message_repo.update(
                msg,
                {
                    "content": reply_text if reply_text else (error_msg or ""),
                    "artifacts": artifacts,
                    "tokens": tokens,
                    "cost_usd": cost_usd,
                    "latency_ms": latency_ms,
                    "is_error": error_msg is not None,
                },
            )
        session = await session_repo.get_by_id(uuid.UUID(session_id))
        if session:
            await session_repo.update(
                session,
                {
                    "message_count": (session.message_count or 0) + 2,
                    "total_cost_usd": (session.total_cost_usd or 0.0) + cost_usd,
                    "total_tokens": (session.total_tokens or 0) + tokens,
                },
            )

    # Terminal event AFTER persistence: the SSE terminal frame is the
    # client's cue to refetch — emitting it before the DB write raced the
    # refetch and served stale transcripts/counts.
    await emitter.emit(*terminal_event)

    # Retained snapshot for late subscribers: app runs have no execution
    # row, so a WebSocket that attaches after the run finished (sub-second
    # graphs) would otherwise see nothing at all.
    try:
        from apps.api.app.core.redis import get_redis

        redis = await get_redis()
        await redis.set(
            f"execution:{execution_id}:snapshot",
            json.dumps(
                {
                    "node_statuses": node_statuses,
                    "terminal": {"type": terminal_event[0], **terminal_event[1]},
                }
            ),
            ex=3600,
        )
    except Exception:  # noqa: BLE001
        logger.warning("could not retain execution snapshot", exc_info=True)


def _walk_dict(obj):
    """Recursively yield every dict value in obj — for usage aggregation."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield v
            yield from _walk_dict(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_dict(item)


def _extract_reply(output: dict) -> tuple[str, list[dict]]:
    """Pull a text reply + artifact list from a workflow's final output.

    Nodes emit their final output under `output_data` on `NodeResult`.
    We look for the most common assistant-reply shapes:
    - agent nodes → `output.content` (str)
    - evaluator/planner → `output.tasks` / `output.scores` (rendered as JSON)
    - anything with `artifacts` list is forwarded
    """
    text = ""
    artifacts: list[dict] = []
    if isinstance(output, dict):
        if isinstance(output.get("content"), str):
            text = output["content"]
        arts = output.get("artifacts")
        if isinstance(arts, list):
            artifacts = arts
    return text, artifacts


@celery_app.task(name="sweep_app_sessions")
def sweep_app_sessions():
    """Nightly: drop AppSession rows with no messages in the last 60 days.

    Keeps the analytics tab focused on active users and stops the sessions
    table from ballooning. Cascade delete on session_id removes the
    orphaned AppMessage rows automatically.
    """
    try:
        asyncio.run(_sweep_app_sessions())
    except Exception as e:
        logger.error(f"sweep_app_sessions failed: {e}", exc_info=True)


async def _sweep_app_sessions():
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import delete, select

    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.features.apps.models import AppMessage, AppSession

    cutoff = datetime.now(UTC) - timedelta(days=60)
    async with AsyncSessionLocal() as db:
        # Find candidate sessions whose last_seen_at is stale AND have zero
        # recent messages. Two-step so we don't cascade an active thread by
        # accident when `last_seen_at` lags message writes.
        stale_ids: list[str] = []
        result = await db.execute(select(AppSession.id).where(AppSession.last_seen_at < cutoff))
        for row in result.scalars().all():
            recent = await db.execute(
                select(AppMessage.id)
                .where(AppMessage.session_id == row, AppMessage.created_at >= cutoff)
                .limit(1)
            )
            if recent.first() is None:
                stale_ids.append(row)
        if stale_ids:
            await db.execute(delete(AppSession).where(AppSession.id.in_(stale_ids)))
            await db.commit()
            logger.info(f"sweep_app_sessions: dropped {len(stale_ids)} stale sessions")
