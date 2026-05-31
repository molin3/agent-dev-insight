"""Evaluation 服务 — 编排评估器"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

# 导入内置评估器以触发注册
from app.evaluators.builtin import completion_rate  # noqa: F401
from app.evaluators.builtin import hallucination  # noqa: F401
from app.evaluators.builtin import latency  # noqa: F401
from app.evaluators.builtin import token_cost  # noqa: F401
from app.evaluators.builtin import tool_accuracy  # noqa: F401
from app.evaluators.builtin import llm_quality  # noqa: F401
from app.evaluators.registry import EvaluatorRegistry
from app.models.score import Score
from app.services.trace_service import TraceService

logger = logging.getLogger(__name__)

BUILTIN_EVALUATORS = [
    "completion_rate",
    "tool_accuracy",
    "latency",
    "token_cost",
    "hallucination",
    "llm_quality",
]


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_trace(
        self,
        trace_id: str,
        evaluator_names: list[str] | None = None,
    ) -> list[Score]:
        trace_service = TraceService(self.db)
        trace = await trace_service.get_trace(trace_id)
        if trace is None:
            return []

        # 删除旧的同名评分，防止重复累加
        from sqlalchemy import delete as sa_delete
        await self.db.execute(
            sa_delete(Score).where(Score.trace_id == trace_id)
        )

        spans = await trace_service.get_spans_for_trace(trace_id)
        names = evaluator_names or BUILTIN_EVALUATORS

        all_scores: list[Score] = []
        for name in names:
            evaluator = EvaluatorRegistry.create(name)
            if evaluator is None:
                logger.warning("Unknown evaluator: %s", name)
                continue

            try:
                scores = await evaluator.evaluate(trace, spans)
                for score in scores:
                    self.db.add(score)
                all_scores.extend(scores)
                logger.info(
                    "Evaluator %s produced %d scores for trace %s",
                    name,
                    len(scores),
                    trace_id,
                )
            except Exception as e:
                logger.error("Evaluator %s failed: %s", name, e)

        await self.db.commit()
        return all_scores

    async def get_evaluator_list(self) -> list[dict]:
        evaluators = EvaluatorRegistry.get_all()
        return [
            {"name": name, "class": cls.__name__}
            for name, cls in evaluators.items()
        ]
