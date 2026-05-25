"""LangChain / LangGraph 回调处理器

通过 LangChain 的 BaseCallbackHandler 拦截 LLM 和 Tool 调用，
自动创建对应的 Span 和 Generation。
"""

import logging
import uuid
from typing import Optional

from .client import AgentDevInsight, get_client

logger = logging.getLogger("agentdevinsight.callback")


class AgentDevInsightCallbackHandler:
    """LangChain 兼容的回调处理器

    用法：
        from agentdevinsight.callback_handler import AgentDevInsightCallbackHandler
        handler = AgentDevInsightCallbackHandler(project="my-agent")
        chain.invoke({"query": "..."}, config={"callbacks": [handler]})
    """

    def __init__(self, *, project: str = "default", api_url: str = "http://localhost:8000"):
        self._client = get_client(project=project, api_url=api_url)
        self._active_trace = None
        self._span_stack: list[str] = []

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs) -> None:
        """Chain 开始时创建 Trace"""
        trace_name = serialized.get("name", serialized.get("id", "chain-run"))
        self._trace_ctx = self._client.trace(name=f"chain:{trace_name}")
        self._active_trace = self._trace_ctx.__enter__()

    def on_chain_end(self, outputs: dict, **kwargs) -> None:
        if self._trace_ctx:
            self._trace_ctx.__exit__(None, None, None)
            self._trace_ctx = None
            self._active_trace = None

    def on_llm_start(self, serialized: dict, prompts: list, **kwargs) -> None:
        if self._active_trace is None:
            trace_name = serialized.get("name", "llm-call")
            self._trace_ctx = self._client.trace(name=f"llm:{trace_name}")
            self._active_trace = self._trace_ctx.__enter__()

        span_name = serialized.get("name", "llm")
        self._span_ctx = self._active_trace.span(
            name=f"llm:{span_name}",
            type="llm",
            input={"prompts": [str(p)[:500] for p in prompts]},
            model=kwargs.get("invocation_params", {}).get("model", "unknown"),
        )
        self._current_span = self._span_ctx.__enter__()

    def on_llm_end(self, response, **kwargs) -> None:
        if hasattr(self, "_current_span") and self._current_span:
            content = ""
            usage = {}
            model = ""
            if hasattr(response, "generations") and response.generations:
                gen = response.generations[0]
                if hasattr(gen, "message") and hasattr(gen.message, "content"):
                    content = gen.message.content or ""
            if hasattr(response, "llm_output") and response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})
                usage = {
                    "prompt_tokens": token_usage.get("prompt_tokens", 0),
                    "completion_tokens": token_usage.get("completion_tokens", 0),
                    "total_tokens": token_usage.get("total_tokens", 0),
                }
            self._current_span.generation(
                model=model,
                prompt=None,
                completion=content[:2000],
                usage=usage,
            )
            if hasattr(self, "_span_ctx"):
                self._span_ctx.__exit__(None, None, None)
                self._span_ctx = None
                self._current_span = None

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        if self._active_trace:
            tool_name = serialized.get("name", "tool")
            self._tool_ctx = self._active_trace.span(
                name=f"tool:{tool_name}",
                type="tool",
                input={"input": input_str[:1000]},
            )
            self._tool_ctx.__enter__()

    def on_tool_end(self, output: str, **kwargs) -> None:
        if hasattr(self, "_tool_ctx"):
            self._tool_ctx._end(output={"result": str(output)[:1000]})
            self._tool_ctx = None

    def on_chain_error(self, error: Exception, **kwargs) -> None:
        logger.error("Chain error: %s", error)
        if self._trace_ctx:
            self._trace_ctx.__exit__(type(error), error, None)
            self._trace_ctx = None
