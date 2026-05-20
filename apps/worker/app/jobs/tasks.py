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
        asyncio.run(_run_workflow(
            execution_id, workflow_id, graph, trigger_data,
            resume_from=resume_from,
            resume_input=resume_input,
            snapshot=snapshot,
        ))
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
    from apps.api.app.execution_engine.engine.workflow_runner import PauseSignal, WorkflowRunner
    from apps.api.app.repositories.execution_repository import ExecutionRepository
    from apps.api.app.repositories.workflow_repository import WorkflowRepository
    from apps.api.app.services.credential_service import CredentialService

    emitter = RedisEventEmitter(execution_id)
    credentials_list: list[dict[str, Any]] = []

    async with AsyncSessionLocal() as db:
        exec_repo = ExecutionRepository(db)
        wf_repo = WorkflowRepository(db)

        await exec_repo.update_status(uuid.UUID(execution_id), "running")
        await exec_repo.add_log(uuid.UUID(execution_id), "Workflow execution started", level="info")
        await emitter.emit("execution_started", {})

        workflow = await wf_repo.get_by_id(uuid.UUID(workflow_id))
        secrets_dict: dict[str, str] = {}
        if workflow:
            credential_service = CredentialService(db)
            credentials_list = await credential_service.list_decrypted_for_user(workflow.user_id)
            # Load user secrets for {{secrets.KEY}} interpolation
            try:
                import sqlalchemy as sa
                from apps.api.app.models.secret import Secret
                from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
                _enc = AESEncryptionService()
                result = await db.execute(sa.select(Secret).where(Secret.user_id == workflow.user_id))
                for s in result.scalars().all():
                    try:
                        secrets_dict[s.name] = _enc.decrypt(s.encrypted_value)
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Failed to load secrets for workflow {workflow_id}: {e}")
        else:
            logger.error(f"Workflow {workflow_id} not found when fetching credentials")

    async def on_log(
        message: str, level: str = "info", node_id: str | None = None, payload: Any = None
    ) -> None:
        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            await repo.add_log(
                uuid.UUID(execution_id), message, level=level, node_id=node_id, payload=payload
            )

    try:
        async with AsyncSessionLocal() as db:
            runner = WorkflowRunner(
                workflow_id=workflow_id,
                execution_id=execution_id,
                graph=graph,
                db=db,
                on_log=on_log,
                credentials=credentials_list,
                emitter=emitter,
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
            await repo.add_log(uuid.UUID(execution_id), "Workflow execution completed", level="info")
            await emitter.emit("execution_completed", {"status": "completed", "output": output})

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
        await emitter.emit("execution_paused", {
            "node_id": pause.node_id,
            "resume_token": token,
            "resume_schema": pause.resume_schema,
        })
        logger.info(f"Execution {execution_id} paused at node {pause.node_id}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Workflow {workflow_id} failed: {error_msg}")
        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            await repo.update_status(uuid.UUID(execution_id), "failed")
            await repo.add_log(uuid.UUID(execution_id), error_msg, level="error")
            await emitter.emit("execution_failed", {"status": "failed", "error": error_msg})
        raise
