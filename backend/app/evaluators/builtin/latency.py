"""延迟评估器 — 计算 P50/P95/P99"""

from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import EvaluatorRegistry
from app.models.score import Score
from app.models.trace import Span, Trace
from app.utils.helpers import gen_uuid


class LatencyEvaluator(BaseEvaluator):
    """评估延迟分位数，返回 P50/P95/P99 三个 Score"""

    def __init__(self, p95_threshold_ms: float = 5000):
        super().__init__()
        self.p95_threshold_ms = p95_threshold_ms

    async def evaluate(self, trace: Trace, spans: list[Span]) -> list[Score]:
        latencies = sorted(
            [s.latency_ms for s in spans if s.latency_ms is not None]
        )
        if not latencies:
            return []

        n = len(latencies)

        def percentile(p: float) -> float:
            idx = int(p * n)
            return latencies[min(idx, n - 1)]

        p50 = percentile(0.5)
        p95 = percentile(0.95)
        p99 = percentile(0.99)

        scores = [
            Score(
                id=gen_uuid(),
                trace_id=trace.id,
                name="latency_p50",
                value=min(1.0, 2000 / max(p50, 1)),
            ),
            Score(
                id=gen_uuid(),
                trace_id=trace.id,
                name="latency_p95",
                value=min(1.0, self.p95_threshold_ms / max(p95, 1)),
            ),
            Score(
                id=gen_uuid(),
                trace_id=trace.id,
                name="latency_p99",
                value=min(1.0, self.p95_threshold_ms / max(p99, 1)),
            ),
        ]
        return scores


EvaluatorRegistry.register("latency", LatencyEvaluator)
