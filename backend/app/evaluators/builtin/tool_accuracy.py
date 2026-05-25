"""工具调用准确率评估器"""

from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import EvaluatorRegistry
from app.models.score import Score
from app.models.trace import Span, Trace
from app.utils.helpers import gen_uuid


class ToolAccuracyEvaluator(BaseEvaluator):
    """评估工具调用的准确性

    判断标准（满足任一即视为成功）：
    1. status == "completed"
    2. 有 output 数据（工具实际执行过）
    3. 有 Generation 输出（工具返回了结果）
    """

    async def evaluate(self, trace: Trace, spans: list[Span]) -> list[Score]:
        tool_spans = [s for s in spans if s.type == "tool"]

        if not tool_spans:
            return []

        total = len(tool_spans)
        errors = sum(1 for s in tool_spans if s.status == "error")
        succeeded = sum(
            1 for s in tool_spans
            if s.status == "completed"
            or s.output is not None
            or (s.generations and any(g.completion for g in s.generations))
        )

        accuracy = succeeded / total if total > 0 else 0.0

        score = Score(
            id=gen_uuid(),
            trace_id=trace.id,
            name="tool_accuracy",
            value=accuracy,
            comment=f"{succeeded}/{total} 工具调用成功（含已完成/有输出/有返回值）, {errors} 失败",
        )
        return [score]


EvaluatorRegistry.register("tool_accuracy", ToolAccuracyEvaluator)
