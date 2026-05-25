"""Token 消耗评估器 — 汇总 Token 使用和成本"""

from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import EvaluatorRegistry
from app.models.score import Score
from app.models.trace import Span, Trace
from app.utils.helpers import gen_uuid


MODEL_PRICING = {
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-coder": {"input": 0.14, "output": 0.28},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "qwen-max": {"input": 0.50, "output": 2.00},
}


class TokenCostEvaluator(BaseEvaluator):
    """汇总 Token 使用量和成本"""

    async def evaluate(self, trace: Trace, spans: list[Span]) -> list[Score]:
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        for span in spans:
            for gen in span.generations:
                usage = gen.usage or {}
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

                total_input_tokens += prompt_tokens
                total_output_tokens += completion_tokens

                model = gen.model or "unknown"
                pricing = MODEL_PRICING.get(model)
                if pricing:
                    cost = (prompt_tokens / 1_000_000) * pricing["input"] + (
                        completion_tokens / 1_000_000
                    ) * pricing["output"]
                    total_cost += cost

        scores = [
            Score(
                id=gen_uuid(),
                trace_id=trace.id,
                name="total_tokens",
                value=float(total_input_tokens + total_output_tokens),
            ),
            Score(
                id=gen_uuid(),
                trace_id=trace.id,
                name="total_cost",
                value=round(total_cost, 6),
            ),
        ]
        return scores


EvaluatorRegistry.register("token_cost", TokenCostEvaluator)
