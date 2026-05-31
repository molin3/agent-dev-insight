"""幻觉检测评估器 — LLM-as-Judge"""

import logging

from app.core.llm_client import LLMClient
from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import EvaluatorRegistry
from app.models.score import Score
from app.models.trace import Span, Trace
from app.utils.helpers import gen_uuid

logger = logging.getLogger(__name__)

JUDGE_SYSTEM = """你是一个 AI 输出质量评估专家。你的任务是判断 AI 助手的回复是否存在幻觉（即编造了不存在的信息）。

评估标准：
- 工具返回的真实数据是否支撑了 AI 的回复
- AI 是否添加了工具返回中不存在的"事实"
- AI 是否编造了具体的数字、名称、日期等

请只返回一个 JSON 对象，格式如下：
{"score": <0到1之间的小数>, "reason": "<一句话说明评判理由>"}

- score 1.0 = 完全没有幻觉，回复完全基于工具返回
- score 0.5 = 有一定幻觉，部分回复缺乏支撑
- score 0.0 = 严重幻觉，回复与工具返回完全不符"""

JUDGE_PROMPT = """请评估以下 AI 回复是否存在幻觉：

## 工具返回的数据
{tool_outputs}

## AI 的回复
{llm_completion}

请评估 AI 回复是否基于工具返回的真实数据，有无编造信息。"""


class HallucinationEvaluator(BaseEvaluator):
    """使用 LLM-as-Judge 检测幻觉，无 LLM 配置时降级为规则判断"""

    async def evaluate(self, trace: Trace, spans: list[Span]) -> list[Score]:
        llm_spans = [s for s in spans if s.type == "llm"]
        if not llm_spans:
            return []

        tool_spans = [s for s in spans if s.type == "tool"]

        # 收集 LLM 输出和工具输出
        llm_completions = []
        tool_outputs = []
        for span in llm_spans:
            for gen in span.generations:
                if gen.completion:
                    llm_completions.append(gen.completion)
        for span in tool_spans:
            if span.output:
                tool_outputs.append(str(span.output))

        # 尝试 LLM-as-Judge
        try:
            client = LLMClient()
            if client.api_key:
                return await self._llm_judge(trace, llm_completions, tool_outputs)
        except Exception as e:
            logger.warning("LLM-as-Judge failed, falling back to rule-based: %s", e)

        # 降级：规则判断
        return self._rule_based(trace, tool_spans, llm_completions)

    async def _llm_judge(
        self, trace: Trace, llm_completions: list[str], tool_outputs: list[str]
    ) -> list[Score]:
        client = LLMClient()
        prompt = JUDGE_PROMPT.format(
            tool_outputs="\n".join(tool_outputs) if tool_outputs else "(无工具调用)",
            llm_completion="\n".join(llm_completions) if llm_completions else "(无输出)",
        )
        response = await client.chat(prompt=prompt, system=JUDGE_SYSTEM)

        # 解析 JSON 响应
        import json
        try:
            result = json.loads(response.content)
            score = float(result.get("score", 0.5))
            reason = result.get("reason", "LLM-as-Judge 评估完成")
        except (json.JSONDecodeError, ValueError):
            score = 0.5
            reason = "无法解析 LLM 评判结果，返回默认分"

        score_obj = Score(
            id=gen_uuid(),
            trace_id=trace.id,
            name="hallucination_score",
            value=round(max(0.0, min(1.0, score)), 2),
            comment=f"[LLM-Judge] {reason}",
        )
        return [score_obj]

    def _rule_based(
        self, trace: Trace, tool_spans: list[Span], llm_completions: list[str]
    ) -> list[Score]:
        has_tool_support = False
        for tool_span in tool_spans:
            if tool_span.output and tool_span.status == "completed":
                has_tool_support = True
                break

        hallucination_score = 0.8 if has_tool_support else 0.5
        if not tool_spans:
            hallucination_score = 0.7

        score = Score(
            id=gen_uuid(),
            trace_id=trace.id,
            name="hallucination_score",
            value=hallucination_score,
            comment="[规则] 基于工具调用的简单幻觉评估" if has_tool_support else "[规则] 可能缺少工具支撑",
        )
        return [score]


EvaluatorRegistry.register("hallucination", HallucinationEvaluator)
