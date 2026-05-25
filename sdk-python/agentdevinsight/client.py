"""AgentDevInsight HTTP 客户端"""

import logging
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("agentdevinsight")


class _HttpClient:
    """内部 HTTP 客户端，带重试和连接池"""

    def __init__(self, api_url: str, api_key: str | None = None, timeout: int = 5):
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AgentDevInsight-SDK/0.1.0",
        })
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    def post(self, path: str, data: dict) -> dict | None:
        try:
            resp = self.session.post(
                f"{self.api_url}{path}",
                json=data,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("AgentDevInsight API call failed: %s %s", path, e)
            return None


class AgentDevInsight:
    """AgentDevInsight 主客户端

    用法：
        client = AgentDevInsight(project="my-agent")
        with client.trace(name="main") as t:
            with t.span(name="llm-call", type="llm") as span:
                span.generation(prompt=[...], completion="...", model="gpt-4")
    """

    def __init__(
        self,
        *,
        project: str = "default",
        api_url: str = "http://localhost:8000",
        api_key: str | None = None,
    ):
        self.project = project
        self._client = _HttpClient(api_url, api_key)
        self._current_trace: Optional["_TraceContext"] = None

    @contextmanager
    def trace(self, name: str, **kwargs):
        trace_ctx = _TraceContext(
            client=self._client,
            project=self.project,
            name=name,
            **kwargs,
        )
        trace_ctx._start()
        prev = self._current_trace
        self._current_trace = trace_ctx
        try:
            yield trace_ctx
        finally:
            self._current_trace = prev
            trace_ctx._end()


class _TraceContext:
    """Trace 上下文管理器"""

    def __init__(self, client: _HttpClient, project: str, name: str, **kwargs):
        self._client = client
        self._project = project
        self._name = name
        self._trace_id = kwargs.pop("trace_id", str(uuid.uuid4()))
        self._metadata = kwargs.pop("metadata", None)
        self._tags = kwargs.pop("tags", None)
        self._start_time: float = 0
        self._ended = False

    def _start(self):
        self._start_time = time.time()
        self._client.post("/api/public/traces", {
            "id": self._trace_id,
            "name": self._name,
            "projectId": self._project,
            "metadata": self._metadata,
            "tags": self._tags,
        })

    def _end(self):
        if self._ended:
            return
        self._ended = True
        self._client.post(f"/api/traces/{self._trace_id}/complete", {})

    @property
    def id(self) -> str:
        return self._trace_id

    @contextmanager
    def span(self, name: str, type: str = "span", parent_span_id: str | None = None, **kwargs):
        span_id = str(uuid.uuid4())
        model = kwargs.pop("model", None)
        input_data = kwargs.pop("input", None)

        self._client.post("/api/public/spans", {
            "id": span_id,
            "traceId": self._trace_id,
            "name": name,
            "type": type,
            "parentObservationId": parent_span_id,
            "model": model,
            "input": input_data,
        })

        span_ctx = _SpanContext(
            client=self._client,
            trace_id=self._trace_id,
            span_id=span_id,
        )
        span_ctx._start_time = time.time()
        try:
            yield span_ctx
        finally:
            span_ctx._end()

    def score(self, name: str, value: float, comment: str | None = None) -> None:
        self._client.post("/api/public/scores", {
            "traceId": self._trace_id,
            "name": name,
            "value": value,
            "comment": comment,
        })


class _SpanContext:
    """Span 上下文管理器"""

    def __init__(self, client: _HttpClient, trace_id: str, span_id: str):
        self._client = client
        self._trace_id = trace_id
        self._span_id = span_id
        self._start_time: float = 0

    def _end(self, output: dict | None = None, error: str | None = None):
        data: dict = {}
        if output is not None:
            data["output"] = output
        if error:
            data["statusMessage"] = error
        self._client.post("/api/public/spans", {
            "id": self._span_id,
            "traceId": self._trace_id,
            "name": "",
            **data,
        })

    def generation(
        self,
        model: str,
        prompt: list | None = None,
        completion: str | None = None,
        usage: dict | None = None,
        cost: float | None = None,
    ) -> None:
        latency_ms = (time.time() - self._start_time) * 1000 if self._start_time else None
        self._client.post("/api/public/generations", {
            "spanId": self._span_id,
            "model": model,
            "input": prompt,
            "output": completion,
            "usage": usage,
            "metadata": {"cost": cost, "latency_ms": latency_ms},
        })


# 全局客户端单例
_global_client: AgentDevInsight | None = None


def get_client(**kwargs) -> AgentDevInsight:
    global _global_client
    if _global_client is None:
        _global_client = AgentDevInsight(**kwargs)
    return _global_client
