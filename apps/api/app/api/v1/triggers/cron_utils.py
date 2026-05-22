from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.models.user import User

router = APIRouter(prefix="/cron", tags=["cron"])


class CronValidateRequest(BaseModel):
    expression: str
    count: int = 5


@router.post("/validate")
async def validate_cron(
    body: CronValidateRequest,
    current_user: User = Depends(get_current_user),
):
    from croniter import croniter

    expr = body.expression.strip()
    if not croniter.is_valid(expr):
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: '{expr}'")

    now = datetime.now(UTC)
    citer = croniter(expr, now)
    next_runs = [citer.get_next(datetime).isoformat() for _ in range(min(body.count, 10))]

    return {
        "valid": True,
        "expression": expr,
        "next_runs": next_runs,
    }


@router.get("/next-runs")
async def get_next_runs(
    expression: str = Query(...),
    count: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
):
    from croniter import croniter

    expr = expression.strip()
    if not croniter.is_valid(expr):
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: '{expr}'")

    now = datetime.now(UTC)
    citer = croniter(expr, now)
    next_runs = [citer.get_next(datetime).isoformat() for _ in range(count)]

    return {"expression": expr, "next_runs": next_runs}
