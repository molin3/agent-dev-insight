"""任务完成率评估器 — 基于规则判断"""

from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import EvaluatorRegistry
from app.models.score import Score
from app.models.trace import Span, Trace
from app.utils.helpers import gen_uuid


class CompletionRateEvaluator(BaseEvaluator):
    """根据 Trace 完成状态和是否有输出判断完成率

    判断逻辑：
    - Trace error → 0.0
    - Trace completed，有实质性输出且无工具错误 → 0.95
    - Trace completed，有输出但有工具错误 → 0.6
    - Trace completed，无输出 → 0.3
    - 其他状态 → 0.5
    """

    async def evaluate(self, trace: Trace, spans: list[Span]) -> list[Score]:
        if not trace:
            return []
        if trace.status == "error":
            value = 0.0
        elif trace.status == "completed":
            # 检查是否有实质性输出: generation completion 或 span output
            has_output = False
            tool_errors = 0
            for s in spans:
                # Generation 输出
                for g in s.generations:
                    if g.completion:
                        has_output = True
                # Span output (工具返回值、LLM 直接设 output 等)
                if s.output and len(s.output) > 0:
                    has_output = True
                if s.type == "tool" and s.status == "error":
                    tool_errors += 1

            if has_output and tool_errors == 0:
                value = 0.95
            elif has_output:
                value = 0.6
            else:
                value = 0.3
        else:
            value = 0.5

        score = Score(
            id=gen_uuid(),
            trace_id=trace.id,
            name="completion_rate",
            value=value,
            comment=f"Trace 状态: {trace.status}",
        )
        return [score]


EvaluatorRegistry.register("completion_rate", CompletionRateEvaluator)
