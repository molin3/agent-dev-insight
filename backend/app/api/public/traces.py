"""POST /api/public/traces — LangFuse 兼容 Trace 采集"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.trace_service import TraceService
from app.utils.langfuse_compat import trace_from_langfuse

router = APIRouter()


class TraceCreate(BaseModel):
    id: str | None = None
    name: str
    userId: str | None = None
    sessionId: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None
    release: str | None = None
    version: str | None = None
    projectId: str | None = None  # AgentDevInsight extension


VALID_TRACE_KEYS = {
    "trace_id", "name", "user_id", "session_id",
    "tags", "metadata", "release", "version",
}


@router.post("/traces", status_code=201)
async def create_trace(
    request: TraceCreate,
    db: AsyncSession = Depends(get_db),
):
    data = trace_from_langfuse(request.model_dump(exclude_none=True))
    project_id = data.pop("project_id", "default")
    data = {k: v for k, v in data.items() if k in VALID_TRACE_KEYS}

    service = TraceService(db)
    trace = await service.create_trace(project_id=project_id, **data)
    return {
        "code": 201,
        "message": "Trace created",
        "data": {"id": trace.id},
    }


@router.get("/traces")
async def list_traces(
    project_id: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = TraceService(db)
    result = await service.get_traces(
        project_id=project_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return {"code": 200, "message": "success", "data": result}
