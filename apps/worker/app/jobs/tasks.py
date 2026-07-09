from __future__ import annotations

import asyncio
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
    published_app_id: str,
    session_id: str,
    assistant_message_id: str,
    user_message: str,
    form_data: dict | None = None,
):
    """Run one turn of a published-app chat.

    Loads the pinned graph snapshot, injects the visitor's message +
    session history + user_id as the trigger payload, streams events
    over the same Redis pub/sub channel the SSE endpoint subscribes to,
    then persists the final assistant reply + artifacts on the
    AppMessage placeholder.
    """
    try:
        asyncio.run(
            _run_app_message(
                execution_id,
                published_app_id,
                session_id,
                assistant_message_id,
                user_message,
                form_data or {},
            )
        )
    except Exception as e:
        logger.error(f"execute_app_message task failed: {e}", exc_info=True)


async def _run_app_message(
    execution_id: str,
    published_app_id: str,
    session_id: str,
    assistant_message_id: str,
    user_message: str,
    form_data: dict,
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
        PublishedAppRepository,
    )
    from apps.api.app.features.credentials.service import CredentialService

    started_at = time.time()

    workspace_id_str: str | None = None
    credentials_list: list[dict[str, Any]] = []
    graph: dict[str, Any] = {}
    history_messages: list[dict[str, Any]] = []
    allow_history = True
    persona_id: str | None = None
    user_id_for_run: uuid.UUID | None = None

    async with AsyncSessionLocal() as db:
        app_repo = PublishedAppRepository(db)
        session_repo = AppSessionRepository(db)
        message_repo = AppMessageRepository(db)
        app = await app_repo.get_by_id(uuid.UUID(published_app_id))
        if not app:
            logger.error(f"published app {published_app_id} not found")
            return
        session = await session_repo.get_by_id(uuid.UUID(session_id))
        if not session:
            logger.error(f"app session {session_id} not found")
            return
        workspace_id_str = str(app.workspace_id)
        graph = app.graph_snapshot or {"nodes": [], "edges": []}
        cfg = app.config or {}
        allow_history = bool(cfg.get("allow_history", True))
        persona_id = cfg.get("system_persona_id")
        user_id_for_run = app.published_by  # crew/agent runs charge against publisher

        # Load prior messages when history is on.
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
    error_msg: str | None = None
    tokens = 0
    cost_usd = 0.0

    try:
        async with AsyncSessionLocal() as db:
            runner = WorkflowRunner(
                workflow_id=str(app.workflow_id),
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
            final_output = await runner.run(trigger_data) or {}
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

        await emitter.emit(
            "execution_completed",
            {"status": "completed", "output": final_output},
        )
    except CancelledException:
        await emitter.emit("execution_cancelled", {"status": "cancelled"})
        error_msg = "Cancelled"
    except Exception as e:
        error_msg = str(e)
        logger.error(f"app-message execution {execution_id} failed: {error_msg}")
        await emitter.emit("execution_failed", {"status": "failed", "error": error_msg})

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
