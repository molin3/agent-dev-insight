"""POST /api/public/generations — LangFuse 兼容 Generation 采集"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.trace_service import TraceService
from app.utils.langfuse_compat import generation_from_langfuse

router = APIRouter()


class GenerationCreate(BaseModel):
    id: str | None = None
    traceId: str | None = None
    spanId: str
    name: str | None = None
    model: str
    input: list | None = None
    output: str | None = None
    usage: dict | None = None
    metadata: dict | None = None


@router.post("/generations", status_code=201)
async def create_generation(
    request: GenerationCreate,
    db: AsyncSession = Depends(get_db),
):
    data = generation_from_langfuse(request.model_dump(exclude_none=True))
    service = TraceService(db)
    gen = await service.create_generation(**data)
    return {
        "code": 201,
        "message": "Generation created",
        "data": {"id": gen.id},
    }
