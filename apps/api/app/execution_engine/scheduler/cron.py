from datetime import UTC

from apps.api.app.core.celery import celery_app
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

REDIS_KEY_PREFIX = "runmycrew:cron:last_run"


@celery_app.task(name="check_cron_triggers")
def check_cron_triggers():
    import asyncio

    asyncio.run(_check_and_fire())


async def _check_and_fire():
    from datetime import datetime

    from croniter import croniter

    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.core.redis import get_redis
    from apps.api.app.execution_engine.engine import execution_engine
    from apps.api.app.features.workflows.repository import WorkflowRepository

    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        repo = WorkflowRepository(db)
        workflows = await repo.find_by_trigger_type("trigger.cron")

    redis = await get_redis()

    for workflow in workflows:
        nodes = workflow.graph.get("nodes", [])
        for node in nodes:
            if node.get("type") != "trigger.cron":
                continue

            props = node.get("data", {}).get("properties", {})
            cron_expr = props.get("cron_expression", "").strip()
            if not cron_expr:
                continue

            node_id = node.get("id", "unknown")
            redis_key = f"{REDIS_KEY_PREFIX}:{workflow.id}:{node_id}"

            try:
                if not croniter.is_valid(cron_expr):
                    logger.warning(
                        f"Invalid cron expression '{cron_expr}' on workflow {workflow.id}"
                    )
                    continue

                # ── Cron drift policy (Phase 5) ────────────────
                # ``latest`` (default) — fire ONCE for the current
                #   tick, discarding any older missed fires.
                # ``catchup`` — fire for every missed tick (capped at
                #   MAX_CATCHUP_FIRES to stop a long-idle worker from
                #   stampeding the queue).
                # ``skip`` — fire nothing if more than one tick was
                #   missed; useful for "freshest data wins" workloads
                #   where stale fires are worse than no fire.
                drift_policy = getattr(workflow, "cron_drift_policy", None) or "latest"

                citer = croniter(cron_expr, now)
                last_expected: datetime = citer.get_prev(datetime)

                last_run_str = await redis.get(redis_key)
                last_run: datetime | None = None
                if last_run_str:
                    last_run = datetime.fromisoformat(last_run_str.decode())
                    if last_run >= last_expected:
                        continue  # already fired for this window

                # Build list of ticks to fire based on drift policy.
                fires: list[datetime] = []
                if drift_policy == "catchup" and last_run is not None:
                    # Replay every missed tick between last_run and now,
                    # bounded so an idle worker doesn't unleash hundreds
                    # of fires when it wakes up.
                    MAX_CATCHUP_FIRES = 10
                    catchup_iter = croniter(cron_expr, last_run)
                    while True:
                        nxt = catchup_iter.get_next(datetime)
                        if nxt > now:
                            break
                        fires.append(nxt)
                        if len(fires) >= MAX_CATCHUP_FIRES:
                            logger.warning(
                                "cron: catchup capped at %d fires for workflow %s",
                                MAX_CATCHUP_FIRES,
                                workflow.id,
                            )
                            break
                elif drift_policy == "skip" and last_run is not None:
                    # If we're already more than one tick late, the
                    # ``skip`` policy says do nothing.
                    next_after_last = croniter(cron_expr, last_run).get_next(datetime)
                    next_after_that = croniter(cron_expr, next_after_last).get_next(datetime)
                    if now >= next_after_that:
                        logger.info(
                            "cron: skip-policy dropped late fire for workflow %s",
                            workflow.id,
                        )
                        await redis.set(redis_key, now.isoformat(), ex=120)
                        continue
                    fires.append(last_expected)
                else:
                    # Default: one fire for the current tick.
                    fires.append(last_expected)

                for scheduled in fires:
                    logger.info(
                        "Firing cron trigger on workflow %s (expr=%s, scheduled=%s)",
                        workflow.id,
                        cron_expr,
                        scheduled.isoformat(),
                    )
                    async with AsyncSessionLocal() as db:
                        wf_repo = WorkflowRepository(db)
                        fresh_workflow = await wf_repo.get_by_id(workflow.id)
                        if not fresh_workflow:
                            continue

                        await execution_engine.trigger_workflow(
                            workflow_id=fresh_workflow.id,
                            graph=fresh_workflow.graph,
                            trigger_type="trigger.cron",
                            input_data={
                                "fired_at": now.isoformat(),
                                "scheduled_time": scheduled.isoformat(),
                                "workflow_id": str(fresh_workflow.id),
                                "cron_expression": cron_expr,
                                "drift_policy": drift_policy,
                            },
                        )

                # Mark as fired — TTL of 2 minutes (safe overlap buffer)
                await redis.set(redis_key, now.isoformat(), ex=120)

            except Exception as e:
                logger.error(
                    f"Cron scheduler error for workflow {workflow.id} node {node_id}: {e}",
                    exc_info=True,
                )
