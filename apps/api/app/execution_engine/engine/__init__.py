import uuid

from sqlalchemy import select

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.core.logger import get_logger
from apps.api.app.features.executions.models import Execution

logger = get_logger(__name__)


class ExecutionEngine:
    async def trigger_workflow(
        self,
        workflow_id: uuid.UUID,
        graph: dict,
        trigger_type: str = "manual",
        input_data: dict | None = None,
    ) -> uuid.UUID:
        async with AsyncSessionLocal() as db:
            # Create Execution record (status: pending)
            execution = Execution(
                workflow_id=workflow_id,
                trigger_type=trigger_type,
                status="pending",
                input_data=input_data or {},
            )
            db.add(execution)
            await db.commit()
            await db.refresh(execution)

            execution_id = execution.id

        # Enqueue Celery task AFTER DB commit (so worker can query it)
        from apps.worker.app.jobs.tasks import execute_workflow

        execute_workflow.delay(
            execution_id=str(execution_id),
            workflow_id=str(workflow_id),
            graph=graph,
            trigger_data=input_data or {},
        )

        logger.info(f"Enqueued execution {execution_id} for workflow {workflow_id}")
        return execution_id

    async def dispatch_existing(
        self,
        execution_id: uuid.UUID,
        workflow_id: uuid.UUID,
        graph: dict,
        trigger_type: str,
        input_data: dict | None = None,
    ) -> None:
        """Enqueue an execution row that was pre-created in `waiting` state.

        Used by the listen-slot path: the editor opens the WS to a row
        that exists but hasn't fired yet, then the matching webhook calls
        this to flip the row to `pending` and hand it off to a Celery
        worker. The execution_id stays stable so the WS subscription
        doesn't have to reconnect.
        """
        async with AsyncSessionLocal() as db:
            row = (
                await db.execute(select(Execution).where(Execution.id == execution_id))
            ).scalar_one_or_none()
            if row is None:
                # Listen slot referenced an execution row that was deleted
                # (cancelled while we were claiming) — log + skip.
                logger.warning(f"dispatch_existing: execution {execution_id} not found, skipping")
                return
            row.status = "pending"
            row.trigger_type = trigger_type
            row.input_data = input_data or {}
            await db.commit()

        from apps.worker.app.jobs.tasks import execute_workflow

        execute_workflow.delay(
            execution_id=str(execution_id),
            workflow_id=str(workflow_id),
            graph=graph,
            trigger_data=input_data or {},
        )
        logger.info(f"Dispatched waiting execution {execution_id} for workflow {workflow_id}")


execution_engine = ExecutionEngine()
