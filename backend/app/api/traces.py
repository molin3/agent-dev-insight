"""内部 Trace 管理 API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.trace_service import TraceService

router = APIRouter()


@router.get("/traces")
async def list_traces(
    project_id: str | None = Query(None),
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = TraceService(db)
    result = await service.get_traces(
        project_id=project_id,
        status=status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return {"code": 200, "message": "success", "data": result}


@router.get("/traces/{trace_id}")
async def get_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TraceService(db)
    trace = await service.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": trace.id,
            "project_id": trace.project_id,
            "name": trace.name,
            "status": trace.status,
            "started_at": trace.started_at.isoformat() if trace.started_at else None,
            "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
            "total_latency_ms": trace.total_latency_ms,
            "total_tokens": trace.total_tokens,
            "total_cost": trace.total_cost,
            "error_message": trace.error_message,
            "extra_metadata": trace.extra_metadata,
            "tags": trace.tags,
            "spans": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type,
                    "parent_span_id": s.parent_span_id,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                    "latency_ms": s.latency_ms,
                    "status": s.status,
                    "model": s.model,
                    "input": s.input,
                    "output": s.output,
                    "usage": s.usage,
                    "cost": s.cost,
                    "error_message": s.error_message,
                    "level": s.level,
                    "generations": [
                        {
                            "id": g.id,
                            "model": g.model,
                            "prompt": g.prompt,
                            "completion": g.completion,
                            "usage": g.usage,
                            "cost": g.cost,
                            "latency_ms": g.latency_ms,
                        }
                        for g in s.generations
                    ],
                }
                for s in trace.spans
            ],
            "scores": [
                {
                    "id": sc.id,
                    "name": sc.name,
                    "value": sc.value,
                    "comment": sc.comment,
                }
                for sc in trace.scores
            ],
        },
    }


@router.get("/traces/{trace_id}/spans")
async def get_trace_spans(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TraceService(db)
    spans = await service.get_spans_for_trace(trace_id)
    return {
        "code": 200,
        "message": "success",
        "data": {"spans": [s.to_dict() for s in spans]},
    }


@router.get("/traces/{trace_id}/replay")
async def get_trace_replay(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TraceService(db)
    events = await service.get_trace_replay(trace_id)
    return {"code": 200, "message": "success", "data": {"events": events}}


@router.post("/traces/{trace_id}/complete")
async def complete_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.core.config import settings

    service = TraceService(db)
    trace = await service.complete_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    # Celery 模式下异步触发评估
    if settings.sdk_ingestion_mode == "celery":
        from app.tasks.trace_tasks import finalize_trace
        finalize_trace.delay(trace_id)

    return {"code": 200, "message": "Trace completed", "data": trace.to_dict()}


@router.delete("/traces/{trace_id}")
async def delete_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TraceService(db)
    deleted = await service.delete_trace(trace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {"code": 200, "message": "Trace deleted", "data": None}
