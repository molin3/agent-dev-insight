"""Score 服务"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score import Score
from app.utils.helpers import gen_uuid


class ScoreService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        span_id: str | None = None,
        comment: str | None = None,
        config_id: str | None = None,
        metadata: dict | None = None,
    ) -> Score:
        score = Score(
            id=gen_uuid(),
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            value=value,
            comment=comment,
            config_id=config_id,
            extra_metadata=metadata,
        )
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)
        return score

    async def get_scores_for_trace(self, trace_id: str) -> list[Score]:
        result = await self.db.execute(
            select(Score).where(Score.trace_id == trace_id)
        )
        return list(result.scalars().all())

    async def delete_score(self, score_id: str) -> bool:
        result = await self.db.execute(select(Score).where(Score.id == score_id))
        score = result.scalar_one_or_none()
        if score is None:
            return False
        await self.db.delete(score)
        await self.db.commit()
        return True
