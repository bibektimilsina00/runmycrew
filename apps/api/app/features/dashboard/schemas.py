from sqlmodel import SQLModel


class DashboardStatItem(SQLModel):
    label: str
    value: str
    unit: str
    delta: str
    delta_dir: str
    spark: list[float]


class DashboardRecentRun(SQLModel):
    id: str
    status: str
    name: str
    trigger: str | None
    duration: str
    ago: str


class DashboardScheduleItem(SQLModel):
    workflow_id: str
    name: str
    time: str
    sub: str
    next_iso: str


class DashboardConnectionItem(SQLModel):
    id: str
    name: str
    type: str
    state: str


class DashboardStatsResponse(SQLModel):
    stats: list[DashboardStatItem]
    recent_runs: list[DashboardRecentRun]
    schedules: list[DashboardScheduleItem]
    connections: list[DashboardConnectionItem]
    total_today: int
