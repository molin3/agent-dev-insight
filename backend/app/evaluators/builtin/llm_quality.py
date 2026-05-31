"""LLM 回复质量评估器 — LLM-as-Judge"""

import logging

from app.core.llm_client import LLMClient
from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import EvaluatorRegistry
from app.models.score import Score
from app.models.trace import Span, Trace
from app.utils.helpers import gen_uuid

logger = logging.getLogger(__name__)

QUALITY_SYSTEM = """你是一个 AI Agent 输出质量评估专家。请从以下维度评估 AI 助手的回复质量：

1. 相关性：回复是否与用户问题相关
2. 完整性：回复是否充分回答了问题
3. 准确性：回复中的信息是否准确

请只返回一个 JSON 对象：
{"score": <0到1之间的小数>, "reason": "<一句话说明评判理由>"}

- score 1.0 = 优秀，完全满足所有维度
- score 0.7 = 良好，基本满足但有小瑕疵
- score 0.5 = 一般，部分满足
- score 0.3 = 较差，多数维度不满足"""

QUALITY_PROMPT = """请评估以下 AI 回复的质量：

## 用户的输入
{user_input}

## AI 的回复
{llm_completion}

请从相关性、完整性、准确性三个维度评估回复质量。"""


class LLMQualityEvaluator(BaseEvaluator):
    """使用 LLM-as-Judge 评估 Agent 回复的整体质量"""

    async def evaluate(self, trace: Trace, spans: list[Span]) -> list[Score]:
        llm_spans = [s for s in spans if s.type == "llm"]
        if not llm_spans:
            return []

        # 收集输入和输出
        llm_completions = []
        user_inputs = []
        for span in llm_spans:
            for gen in span.generations:
                if gen.completion:
                    llm_completions.append(gen.completion)
                if gen.prompt:
                    if isinstance(gen.prompt, list):
                        for msg in gen.prompt:
                            if isinstance(msg, dict) and msg.get("role") == "user":
                                user_inputs.append(str(msg.get("content", "")))
                    else:
                        user_inputs.append(str(gen.prompt))

        if not llm_completions:
            return []

        # 尝试 LLM-as-Judge
        try:
            client = LLMClient()
            if client.api_key:
                return await self._llm_judge(trace, user_inputs, llm_completions)
        except Exception as e:
            logger.warning("LLM quality judge failed, using heuristic: %s", e)

        # 降级：启发式评估
        return self._heuristic(trace, llm_completions)

    async def _llm_judge(
        self, trace: Trace, user_inputs: list[str], llm_completions: list[str]
    ) -> list[Score]:
        client = LLMClient()
        prompt = QUALITY_PROMPT.format(
            user_input="\n".join(user_inputs) if user_inputs else "(无输入)",
            llm_completion="\n".join(llm_completions),
        )
        response = await client.chat(prompt=prompt, system=QUALITY_SYSTEM)

        import json
        try:
            result = json.loads(response.content)
            score = float(result.get("score", 0.5))
            reason = result.get("reason", "LLM 质量评估完成")
        except (json.JSONDecodeError, ValueError):
            score = 0.5
            reason = "无法解析 LLM 评判结果"

        score_obj = Score(
            id=gen_uuid(),
            trace_id=trace.id,
            name="llm_quality",
            value=round(max(0.0, min(1.0, score)), 2),
            comment=f"[LLM-Judge] {reason}",
        )
        return [score_obj]

    def _heuristic(self, trace: Trace, llm_completions: list[str]) -> list[Score]:
        # 启发式：基于回复长度和是否存在判断
        total_len = sum(len(c) for c in llm_completions)
        if total_len > 100:
            value = 0.7
            comment = "[启发式] 回复内容较充分"
        elif total_len > 20:
            value = 0.5
            comment = "[启发式] 回复内容较简短"
        else:
            value = 0.3
            comment = "[启发式] 回复内容过少"

        score = Score(
            id=gen_uuid(),
            trace_id=trace.id,
            name="llm_quality",
            value=value,
            comment=comment,
        )
        return [score]


EvaluatorRegistry.register("llm_quality", LLMQualityEvaluator)
