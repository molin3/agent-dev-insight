"""内部 Score API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.score_service import ScoreService

router = APIRouter()


@router.get("/traces/{trace_id}/scores")
async def get_trace_scores(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ScoreService(db)
    scores = await service.get_scores_for_trace(trace_id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "scores": [s.to_dict() for s in scores],
        },
    }


@router.delete("/scores/{score_id}")
async def delete_score(
    score_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ScoreService(db)
    deleted = await service.delete_score(score_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Score not found")
    return {"code": 200, "message": "Score deleted", "data": None}
