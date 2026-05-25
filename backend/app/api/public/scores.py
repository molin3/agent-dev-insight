"""POST /api/public/scores — LangFuse 兼容 Score 采集"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.score_service import ScoreService
from app.utils.langfuse_compat import score_from_langfuse

router = APIRouter()


class ScoreCreate(BaseModel):
    id: str | None = None
    traceId: str
    observationId: str | None = None
    name: str
    value: float
    comment: str | None = None
    configId: str | None = None


@router.post("/scores", status_code=201)
async def create_score(
    request: ScoreCreate,
    db: AsyncSession = Depends(get_db),
):
    data = score_from_langfuse(request.model_dump(exclude_none=True))
    service = ScoreService(db)
    score = await service.create_score(**data)
    return {
        "code": 201,
        "message": "Score created",
        "data": {"id": score.id},
    }
