"""LangChain / LangGraph callback handler.

Requires the ``langchain`` optional extra::

    pip install agentdevinsight[langchain]
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional, Union

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from .client import AgentDevInsightClient, get_client

logger = logging.getLogger("agentdevinsight.callbacks")


class AgentDevInsightCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler that maps chain / LLM / tool events to
    AgentDevInsight traces, spans and generations.

    Usage::

        from agentdevinsight.callbacks import AgentDevInsightCallbackHandler

        handler = AgentDevInsightCallbackHandler()
        chain.invoke({"query": "..."}, config={"callbacks": [handler]})
    """

    def __init__(
        self,
        *,
        client: AgentDevInsightClient | None = None,
        trace_name: str = "langchain-run",
    ) -> None:
        super().__init__()
        self._client = client or get_client()
        self._trace_name = trace_name

        # Runtime state -------------------------------------------------------
        self._trace_id: Optional[str] = None
        self._active_spans: dict[str, str] = {}  # run_id -> span_id
        self._span_start_times: dict[str, float] = {}

    # -- helpers -------------------------------------------------------------

    def _ensure_trace(self, run_id: Any, name: Optional[str] = None) -> None:
        """Create a trace if one is not already active."""
        if self._trace_id is not None:
            return
        resp = self._client.create_trace(name or self._trace_name)
        if resp and "data" in resp:
            self._trace_id = resp["data"].get("id")
            logger.debug("trace created: %s", self._trace_id)

    def _make_span_id(self, run_id: Any) -> str:
        return str(run_id)

    # -- Chain events --------------------------------------------------------

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        chain_name = (
            serialized.get("name")
            or serialized.get("id", ["chain"])[-1]
            if isinstance(serialized.get("id"), list)
            else serialized.get("id", "chain")
        )
        self._ensure_trace(run_id, name=f"chain:{chain_name}")

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        **kwargs: Any,
    ) -> None:
        # Mark the trace with final output metadata
        if self._trace_id:
            self._client.create_trace(
                self._trace_name,
                id=self._trace_id,
                metadata={"output": outputs, "status": "success"},
            )
        self._trace_id = None

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        **kwargs: Any,
    ) -> None:
        if self._trace_id:
            self._client.create_trace(
                self._trace_name,
                id=self._trace_id,
                metadata={
                    "status": "error",
                    "error": f"{type(error).__name__}: {error}",
                },
            )
        self._trace_id = None

    # -- LLM events ---------------------------------------------------------

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        invocation_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._ensure_trace(run_id)
        if self._trace_id is None:
            return

        model = "unknown"
        if invocation_params:
            model = invocation_params.get("model", "unknown")

        span_id = self._make_span_id(run_id)
        self._active_spans[run_id] = span_id
        self._span_start_times[run_id] = time.time()

        self._client.create_span(
            self._trace_id,
            name=serialized.get("name", "llm"),
            type="llm",
            id=span_id,
            model=model,
            input={"prompts": [p[:500] for p in prompts]},
        )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        **kwargs: Any,
    ) -> None:
        span_id = self._active_spans.pop(run_id, None)
        if span_id is None:
            return

        # Extract completion text
        completion = ""
        if response.generations:
            gen0 = response.generations[0]
            if gen0:
                completion = gen0[0].text if hasattr(gen0[0], "text") else str(gen0[0])

        # Extract token usage
        usage: dict[str, Any] = {}
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            usage = {
                "prompt_tokens": token_usage.get("prompt_tokens", 0),
                "completion_tokens": token_usage.get("completion_tokens", 0),
                "total_tokens": token_usage.get("total_tokens", 0),
            }

        start = self._span_start_times.pop(run_id, 0)
        latency_ms = round((time.time() - start) * 1000, 2) if start else None

        self._client.create_generation(
            span_id,
            model="",
            prompt=None,
            completion=completion[:2000],
            usage=usage,
            metadata={"latency_ms": latency_ms} if latency_ms else None,
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        **kwargs: Any,
    ) -> None:
        self._active_spans.pop(run_id, None)
        self._span_start_times.pop(run_id, None)

    # -- Tool events ---------------------------------------------------------

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        **kwargs: Any,
    ) -> None:
        self._ensure_trace(run_id)
        if self._trace_id is None:
            return

        tool_name = serialized.get("name", "tool")
        span_id = self._make_span_id(run_id)
        self._active_spans[run_id] = span_id
        self._span_start_times[run_id] = time.time()

        self._client.create_span(
            self._trace_id,
            name=f"tool:{tool_name}",
            type="tool",
            id=span_id,
            input={"input": input_str[:1000]},
        )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        **kwargs: Any,
    ) -> None:
        span_id = self._active_spans.pop(run_id, None)
        self._span_start_times.pop(run_id, None)
        if span_id is None or self._trace_id is None:
            return

        self._client.create_span(
            self._trace_id,
            name="",
            id=span_id,
            output={"result": str(output)[:1000]},
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        **kwargs: Any,
    ) -> None:
        span_id = self._active_spans.pop(run_id, None)
        self._span_start_times.pop(run_id, None)
        if span_id is None or self._trace_id is None:
            return

        self._client.create_span(
            self._trace_id,
            name="",
            id=span_id,
            statusMessage=f"{type(error).__name__}: {error}",
        )
