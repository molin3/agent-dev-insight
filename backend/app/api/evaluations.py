"""评估 API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models.score import Score
from app.models.trace import Trace
from app.services.evaluation_service import BUILTIN_EVALUATORS, EvaluationService

router = APIRouter()


class EvaluateRequest(BaseModel):
    evaluator_names: list[str] | None = None


@router.post("/traces/{trace_id}/evaluate")
async def evaluate_trace(
    trace_id: str,
    request: EvaluateRequest = EvaluateRequest(),
    db: AsyncSession = Depends(get_db),
):
    service = EvaluationService(db)
    scores = await service.evaluate_trace(trace_id, request.evaluator_names)
    return {
        "code": 200,
        "message": "Evaluation completed",
        "data": {
            "trace_id": trace_id,
            "score_count": len(scores),
            "scores": [s.to_dict() for s in scores],
        },
    }


@router.get("/evaluators")
async def list_evaluators(db: AsyncSession = Depends(get_db)):
    service = EvaluationService(db)
    evaluators = await service.get_evaluator_list()
    return {
        "code": 200,
        "message": "success",
        "data": {
            "builtin": BUILTIN_EVALUATORS,
            "registered": evaluators,
        },
    }


@router.get("/evaluations")
async def list_evaluations(db: AsyncSession = Depends(get_db)):
    """Batch endpoint: return all completed traces with their scores."""
    stmt = (
        select(Trace)
        .where(Trace.status == "completed")
        .options(joinedload(Trace.scores))
        .order_by(Trace.started_at.desc())
    )
    result = await db.execute(stmt)
    traces = result.unique().scalars().all()

    data = [
        {
            "trace_id": t.id,
            "trace_name": t.name,
            "status": t.status,
            "scores": [{"name": s.name, "value": s.value} for s in t.scores],
        }
        for t in traces
    ]
    return {"code": 200, "message": "success", "data": data}


@router.get("/dashboard/overview")
async def dashboard_overview(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func, case

    # SQL 聚合：一次查询完成所有统计
    stmt = select(
        func.count().label("total_traces"),
        func.sum(case((Trace.status == "completed", 1), else_=0)).label("completed"),
        func.sum(case((Trace.status == "error", 1), else_=0)).label("errors"),
        func.coalesce(func.sum(Trace.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(Trace.total_cost), 0).label("total_cost"),
        func.coalesce(func.avg(Trace.total_latency_ms), 0).label("avg_latency_ms"),
    )
    result = await db.execute(stmt)
    row = result.one()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_traces": row.total_traces or 0,
            "completed": row.completed or 0,
            "errors": row.errors or 0,
            "total_tokens": row.total_tokens or 0,
            "total_cost": round(row.total_cost or 0, 6),
            "avg_latency_ms": round(row.avg_latency_ms or 0, 2),
        },
    }
