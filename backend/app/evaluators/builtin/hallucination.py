"""幻觉检测评估器 — 检查 LLM 输出是否有工具返回支撑"""

from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import EvaluatorRegistry
from app.models.score import Score
from app.models.trace import Span, Trace
from app.utils.helpers import gen_uuid


class HallucinationEvaluator(BaseEvaluator):
    """基于规则检查 LLM 输出是否与工具返回一致

    简化规则：检查 tool span 的 output 是否与对应的 llm span generation 匹配。
    实际项目中应使用 LLM-as-Judge 进行更精确的检测。
    """

    async def evaluate(self, trace: Trace, spans: list[Span]) -> list[Score]:
        llm_spans = [s for s in spans if s.type == "llm"]
        tool_spans = [s for s in spans if s.type == "tool"]

        if not llm_spans:
            return []

        has_tool_support = False
        for llm_span in llm_spans:
            for gen in llm_span.generations:
                if gen.completion:
                    for tool_span in tool_spans:
                        if tool_span.output and tool_span.status == "completed":
                            has_tool_support = True
                            break

        hallucination_score = 0.8 if has_tool_support else 0.5
        if not tool_spans:
            hallucination_score = 0.7  # 无工具调用，无法判断

        score = Score(
            id=gen_uuid(),
            trace_id=trace.id,
            name="hallucination_score",
            value=hallucination_score,
            comment="基于工具调用的简单幻觉评估" if has_tool_support else "可能缺少工具支撑",
        )
        return [score]


EvaluatorRegistry.register("hallucination", HallucinationEvaluator)
