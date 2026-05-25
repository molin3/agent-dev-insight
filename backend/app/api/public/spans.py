"""POST /api/public/spans — LangFuse 兼容 Span 采集"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.trace_service import TraceService
from app.utils.langfuse_compat import span_from_langfuse

router = APIRouter()


class SpanCreate(BaseModel):
    id: str | None = None
    traceId: str
    parentObservationId: str | None = None
    name: str
    type: str = "span"
    input: dict | None = None
    output: dict | None = None
    metadata: dict | None = None
    model: str | None = None
    startTime: str | None = None
    endTime: str | None = None
    usage: dict | None = None
    statusMessage: str | None = None
    level: int = 0


VALID_SPAN_KEYS = {
    "trace_id", "name", "type", "parent_span_id",
    "input", "output", "metadata", "model", "span_id",
    "started_at", "level",
}


@router.post("/spans", status_code=201)
async def create_span(
    request: SpanCreate,
    db: AsyncSession = Depends(get_db),
):
    data = span_from_langfuse(request.model_dump(exclude_none=True))
    data = {k: v for k, v in data.items() if k in VALID_SPAN_KEYS}
    service = TraceService(db)
    span = await service.create_span(**data)
    return {
        "code": 201,
        "message": "Span created",
        "data": {"id": span.id},
    }
