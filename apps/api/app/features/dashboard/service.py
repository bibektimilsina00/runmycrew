from datetime import UTC, datetime, timedelta

import sqlalchemy as sa
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.credentials.models import Credential
from apps.api.app.features.dashboard.schemas import (
    DashboardConnectionItem,
    DashboardRecentRun,
    DashboardScheduleItem,
    DashboardStatItem,
    DashboardStatsResponse,
)
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Execution, Workflow
from apps.api.app.features.workspaces.models import Workspace


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(
        self, current_user: User, workspace: Workspace
    ) -> DashboardStatsResponse:
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        twelve_ago = now - timedelta(hours=12)

        # ── Workflow IDs for this workspace ──────────────────────────────────────
        wf_ids_result = await self.db.execute(
            sa.select(Workflow.id).where(Workflow.workspace_id == workspace.id)
        )
        wf_ids = [r[0] for r in wf_ids_result.fetchall()]

        if not wf_ids:
            return self._empty_stats(current_user)

        # ── Today's runs ─────────────────────────────────────────────────────────
        runs_today = await self._count_executions(wf_ids, today_start, now)
        runs_yesterday = await self._count_executions(wf_ids, yesterday_start, today_start)
        runs_delta_pct = self._pct_change(runs_yesterday, runs_today)

        # ── Success rate today ───────────────────────────────────────────────────
        completed_today = await self._count_executions(wf_ids, today_start, now, status="completed")
        failed_today = await self._count_executions(wf_ids, today_start, now, status="failed")
        total_finished = completed_today + failed_today
        success_rate = (completed_today / total_finished * 100) if total_finished > 0 else 100.0

        completed_yest = await self._count_executions(
            wf_ids, yesterday_start, today_start, status="completed"
        )
        failed_yest = await self._count_executions(
            wf_ids, yesterday_start, today_start, status="failed"
        )
        total_yest = completed_yest + failed_yest
        sr_yest = (completed_yest / total_yest * 100) if total_yest > 0 else 100.0
        sr_delta = round(success_rate - sr_yest, 1)

        # ── Active workflows ─────────────────────────────────────────────────────
        active_wf = await self.db.execute(
            sa.select(sa.func.count()).where(
                Workflow.workspace_id == workspace.id,
                Workflow.is_active.is_(True),
            )
        )
        active_count = active_wf.scalar() or 0

        # ── Hourly sparklines (last 12 hours) ────────────────────────────────────
        runs_spark = await self._hourly_counts(wf_ids, twelve_ago, now, status=None)
        success_spark = await self._hourly_rate(wf_ids, twelve_ago, now)

        # ── Time saved estimate (avg 5 min per automated task) ───────────────────
        time_saved_hrs = round(runs_today * 5 / 60, 1)
        ts_spark = [round(x * 5 / 60, 1) for x in runs_spark]

        # ── Recent runs (last 8) ─────────────────────────────────────────────────
        recent_result = await self.db.execute(
            sa.select(
                Execution.id,
                Execution.status,
                Execution.trigger_type,
                Execution.started_at,
                Execution.finished_at,
                Workflow.name.label("workflow_name"),
            )
            .join(Workflow, Execution.workflow_id == Workflow.id)
            .where(Workflow.workspace_id == workspace.id)
            .order_by(Execution.started_at.desc())
            .limit(8)
        )
        recent_rows = recent_result.fetchall()
        recent_runs = [
            DashboardRecentRun(
                id=str(r.id),
                status=self._map_status(r.status),
                name=r.workflow_name,
                trigger=r.trigger_type,
                duration=self._fmt_duration(r.started_at, r.finished_at),
                ago=self._time_ago(r.started_at),
            )
            for r in recent_rows
        ]

        # ── Next 12 hours schedules ───────────────────────────────────────────────
        schedules = await self._next_schedules(workspace.id, limit=4)
        schedule_items = [DashboardScheduleItem(**s) for s in schedules]

        # ── Connections summary ───────────────────────────────────────────────────
        cred_result = await self.db.execute(
            sa.select(Credential).where(Credential.workspace_id == workspace.id).limit(5)
        )
        credentials = cred_result.scalars().all()
        connections = [
            DashboardConnectionItem(
                id=str(c.id),
                name=c.name,
                type=c.type,
                state=self._cred_state(c),
            )
            for c in credentials
        ]

        return DashboardStatsResponse(
            stats=[
                DashboardStatItem(
                    label="Runs today",
                    value=str(runs_today),
                    unit="",
                    delta=f"{'+' if runs_delta_pct >= 0 else ''}{runs_delta_pct}%",
                    delta_dir="up" if runs_delta_pct >= 0 else "down",
                    spark=runs_spark,
                ),
                DashboardStatItem(
                    label="Success rate",
                    value=str(round(success_rate, 1)),
                    unit="%",
                    delta=f"{'+' if sr_delta >= 0 else ''}{sr_delta}pp",
                    delta_dir="up" if sr_delta >= 0 else "down",
                    spark=success_spark,
                ),
                DashboardStatItem(
                    label="Time saved",
                    value=str(time_saved_hrs),
                    unit="hr",
                    delta=f"+{round(time_saved_hrs * 0.15, 1)}hr",
                    delta_dir="up",
                    spark=ts_spark,
                ),
                DashboardStatItem(
                    label="Active workflows",
                    value=str(active_count),
                    unit="",
                    delta=f"+{max(0, active_count - 1)}",
                    delta_dir="flat",
                    spark=[max(0, active_count - i) for i in range(11, -1, -1)],
                ),
            ],
            recent_runs=recent_runs,
            schedules=schedule_items,
            connections=connections,
            total_today=runs_today,
        )

    def _empty_stats(self, user: User) -> DashboardStatsResponse:
        zero_spark = [0.0] * 12
        return DashboardStatsResponse(
            stats=[
                DashboardStatItem(
                    label="Runs today",
                    value="0",
                    unit="",
                    delta="+0%",
                    delta_dir="flat",
                    spark=zero_spark,
                ),
                DashboardStatItem(
                    label="Success rate",
                    value="100",
                    unit="%",
                    delta="+0pp",
                    delta_dir="flat",
                    spark=[100.0] * 12,
                ),
                DashboardStatItem(
                    label="Time saved",
                    value="0.0",
                    unit="hr",
                    delta="+0hr",
                    delta_dir="flat",
                    spark=zero_spark,
                ),
                DashboardStatItem(
                    label="Active workflows",
                    value="0",
                    unit="",
                    delta="+0",
                    delta_dir="flat",
                    spark=zero_spark,
                ),
            ],
            recent_runs=[],
            schedules=[],
            connections=[],
            total_today=0,
        )

    async def _count_executions(self, wf_ids, start, end, status=None) -> int:
        q = sa.select(sa.func.count(Execution.id)).where(
            Execution.workflow_id.in_(wf_ids),
            Execution.started_at >= start,
            Execution.started_at < end,
        )
        if status:
            q = q.where(Execution.status == status)
        r = await self.db.execute(q)
        return r.scalar() or 0

    async def _hourly_counts(self, wf_ids, start, end, status=None) -> list[float]:
        """12 hourly buckets, oldest → newest."""
        result = []
        bucket_size = (end - start) / 12
        for i in range(12):
            b_start = start + i * bucket_size
            b_end = b_start + bucket_size
            q = sa.select(sa.func.count(Execution.id)).where(
                Execution.workflow_id.in_(wf_ids),
                Execution.started_at >= b_start,
                Execution.started_at < b_end,
            )
            if status:
                q = q.where(Execution.status == status)
            r = await self.db.execute(q)
            result.append(float(r.scalar() or 0))
        return result

    async def _hourly_rate(self, wf_ids, start, end) -> list[float]:
        """Success rate % per hour bucket."""
        bucket_size = (end - start) / 12
        result = []
        for i in range(12):
            b_start = start + i * bucket_size
            b_end = b_start + bucket_size
            total = await self._count_executions(wf_ids, b_start, b_end)
            ok = await self._count_executions(wf_ids, b_start, b_end, status="completed")
            result.append(round(ok / total * 100, 1) if total > 0 else 100.0)
        return result

    async def _next_schedules(self, workspace_id, limit=4) -> list[dict]:
        wf_result = await self.db.execute(
            sa.select(Workflow).where(
                Workflow.workspace_id == workspace_id,
                Workflow.is_active.is_(True),
            )
        )
        workflows = wf_result.scalars().all()

        items = []
        for wf in workflows:
            nodes = (wf.graph or {}).get("nodes", [])
            for node in nodes:
                if node.get("type") != "trigger.cron":
                    continue
                props = (node.get("data") or {}).get("properties") or {}
                expr = props.get("cron_expression", "")
                tz = props.get("timezone", "UTC")
                if not expr:
                    continue
                try:
                    import datetime as _dt
                    from zoneinfo import ZoneInfo

                    from croniter import croniter

                    zone = ZoneInfo(tz)
                    ci = croniter(expr, _dt.datetime.now(zone))
                    nxt = ci.get_next(_dt.datetime)
                    items.append(
                        {
                            "workflow_id": str(wf.id),
                            "name": wf.name,
                            "time": nxt.strftime("%H:%M"),
                            "sub": expr,
                            "next_iso": nxt.isoformat(),
                        }
                    )
                except Exception:
                    pass

        # Sort by next run time
        items.sort(key=lambda x: x["next_iso"])
        return items[:limit]

    def _pct_change(self, old: int, new: int) -> float:
        if old == 0:
            return 100.0 if new > 0 else 0.0
        return round((new - old) / old * 100, 1)

    def _map_status(self, status: str) -> str:
        if status == "completed":
            return "ok"
        if status == "failed":
            return "err"
        if status == "running":
            return "run"
        return "warn"

    def _fmt_duration(self, started_at, finished_at) -> str:
        if not started_at:
            return "—"
        if not finished_at:
            return "running"
        diff = (finished_at - started_at).total_seconds()
        if diff < 60:
            return f"{diff:.1f}s"
        return f"{int(diff // 60)}m {int(diff % 60)}s"

    def _time_ago(self, dt) -> str:
        if not dt:
            return "—"
        from datetime import UTC

        now = datetime.now(UTC)
        ts = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt
        diff = int((now - ts).total_seconds())
        if diff < 60:
            return "now"
        if diff < 3600:
            return f"{diff // 60}m ago"
        if diff < 86400:
            return f"{diff // 3600}h ago"
        return f"{diff // 86400}d ago"

    def _cred_state(self, cred) -> str:
        meta = cred.meta or {}
        exp = meta.get("expires_at")
        if not exp:
            return "ok"
        try:
            from datetime import UTC

            exp_dt = datetime.fromisoformat(exp)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=UTC)
            diff = (exp_dt - datetime.now(UTC)).total_seconds()
            if diff < 0:
                return "err"
            if diff < 7 * 86400:
                return "warn"
        except Exception:
            pass
        return "ok"


def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(db)
