"""评估 API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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


@router.get("/dashboard/overview")
async def dashboard_overview(db: AsyncSession = Depends(get_db)):
    from app.services.trace_service import TraceService

    trace_service = TraceService(db)
    result = await trace_service.get_traces(page=1, page_size=1000)
    traces = result["items"]

    total_traces = result["total"]
    completed = sum(1 for t in traces if t.status == "completed")
    errors = sum(1 for t in traces if t.status == "error")
    total_tokens = sum(t.total_tokens or 0 for t in traces)
    total_cost = sum(t.total_cost or 0 for t in traces)
    avg_latency = (
        sum(t.total_latency_ms or 0 for t in traces) / len(traces)
        if traces
        else 0
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_traces": total_traces,
            "completed": completed,
            "errors": errors,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 2),
        },
    }
