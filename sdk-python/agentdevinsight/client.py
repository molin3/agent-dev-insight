"""AgentDevInsight HTTP client — core SDK module."""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import contextmanager
from typing import Any, Generator, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("agentdevinsight")

_DEFAULT_BASE_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Internal HTTP layer with retry + connection pooling
# ---------------------------------------------------------------------------

class _HttpClient:
    """Thin wrapper around ``requests.Session`` with retry and connection pool."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AgentDevInsight-SDK/0.1.0",
        })
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    # ----- HTTP helpers -----------------------------------------------------

    def post(self, path: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """POST JSON to ``path``. Returns parsed JSON or *None* on failure."""
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.post(url, json=data, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            logger.warning("AgentDevInsight API call failed: POST %s", path, exc_info=True)
            return None

    def put(self, path: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """PUT JSON to ``path``. Returns parsed JSON or *None* on failure."""
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.put(url, json=data, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            logger.warning("AgentDevInsight API call failed: PUT %s", path, exc_info=True)
            return None


# ---------------------------------------------------------------------------
# Public client
# ---------------------------------------------------------------------------

class AgentDevInsightClient:
    """High-level client for the AgentDevInsight public API.

    Usage::

        from agentdevinsight import AgentDevInsightClient

        client = AgentDevInsightClient()          # reads env vars
        trace  = client.create_trace("my-run")
        span   = client.create_span(trace["data"]["id"], "llm-call", type="llm")
        client.create_generation(span["data"]["id"], model="gpt-4", prompt="Hello")
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 10,
    ):
        self._http = _HttpClient(
            base_url=base_url or os.getenv("AGENTDEVINSIGHT_BASE_URL", _DEFAULT_BASE_URL),
            api_key=api_key or os.getenv("AGENTDEVINSIGHT_API_KEY"),
            timeout=timeout,
        )

    # ----- REST-style CRUD methods ------------------------------------------

    def create_trace(self, name: str, **kwargs: Any) -> Optional[dict[str, Any]]:
        """Create a new trace.

        Parameters
        ----------
        name : str
            Human-readable trace name.
        **kwargs :
            Additional LangFuse-compatible fields (``id``, ``userId``,
            ``sessionId``, ``tags``, ``metadata``, ``release``, ``version``).
        """
        payload: dict[str, Any] = {"name": name, **kwargs}
        payload.setdefault("id", str(uuid.uuid4()))
        logger.debug("create_trace %s", payload.get("id"))
        return self._http.post("/api/public/traces", payload)

    def create_span(
        self,
        trace_id: str,
        name: str,
        *,
        type: str = "span",
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """Create a span under an existing trace.

        Parameters
        ----------
        trace_id : str
            Parent trace id (returned by ``create_trace``).
        name : str
            Span name.
        type : str
            Span type (``"span"``, ``"llm"``, ``"tool"``, ...).
        **kwargs :
            ``parentObservationId``, ``input``, ``output``, ``metadata``,
            ``model``, ``startTime``, ``endTime``, ``statusMessage``, ``level``.
        """
        payload: dict[str, Any] = {
            "traceId": trace_id,
            "name": name,
            "type": type,
            **kwargs,
        }
        payload.setdefault("id", str(uuid.uuid4()))
        logger.debug("create_span %s (trace=%s)", payload.get("id"), trace_id)
        return self._http.post("/api/public/spans", payload)

    def create_generation(
        self,
        span_id: str,
        model: str,
        prompt: Any | None = None,
        completion: Any | None = None,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """Create a generation (LLM call record) under a span.

        Parameters
        ----------
        span_id : str
            Parent span / observation id.
        model : str
            Model identifier (e.g. ``"gpt-4"``).
        prompt : list | str | None
            Prompt(s) sent to the model.
        completion : str | None
            Model completion text.
        **kwargs :
            ``traceId``, ``name``, ``usage``, ``metadata``.
        """
        payload: dict[str, Any] = {
            "spanId": span_id,
            "model": model,
            **kwargs,
        }
        if prompt is not None:
            payload["input"] = prompt if isinstance(prompt, list) else [prompt]
        if completion is not None:
            payload["output"] = completion
        payload.setdefault("id", str(uuid.uuid4()))
        logger.debug("create_generation %s (span=%s)", payload.get("id"), span_id)
        return self._http.post("/api/public/generations", payload)

    def create_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """Attach an evaluation score to a trace.

        Parameters
        ----------
        trace_id : str
            Target trace id.
        name : str
            Score name (e.g. ``"quality"``).
        value : float
            Numeric value.
        **kwargs :
            ``observationId``, ``comment``, ``configId``.
        """
        payload: dict[str, Any] = {
            "traceId": trace_id,
            "name": name,
            "value": value,
            **kwargs,
        }
        payload.setdefault("id", str(uuid.uuid4()))
        logger.debug("create_score trace=%s name=%s value=%s", trace_id, name, value)
        return self._http.post("/api/public/scores", payload)

    # ----- Context-manager helpers ------------------------------------------

    @contextmanager
    def trace(self, name: str, **kwargs: Any) -> Generator[_TraceContext, None, None]:
        """Context manager that creates a trace and auto-completes on exit.

        Usage::

            with client.trace("my-agent") as t:
                with t.span("llm", type="llm") as s:
                    s.generation(model="gpt-4", prompt="hi", completion="hello")
        """
        trace_id = kwargs.pop("trace_id", str(uuid.uuid4()))
        ctx = _TraceContext(client=self, trace_id=trace_id, name=name, **kwargs)
        ctx._start()
        yield ctx
        ctx._end()


# ---------------------------------------------------------------------------
# Context helpers (used by decorator & callback handler)
# ---------------------------------------------------------------------------

class _TraceContext:
    """Returned by ``AgentDevInsightClient.trace()`` context manager."""

    def __init__(self, client: AgentDevInsightClient, trace_id: str, name: str, **kwargs: Any):
        self._client = client
        self._trace_id = trace_id
        self._name = name
        self._metadata = kwargs.pop("metadata", None)
        self._tags = kwargs.pop("tags", None)
        self._extra = kwargs
        self._ended = False

    # -- lifecycle -----------------------------------------------------------

    def _start(self) -> None:
        self._client.create_trace(
            self._name,
            trace_id=self._trace_id,
            metadata=self._metadata,
            tags=self._tags,
            **self._extra,
        )

    def _end(self) -> None:
        if self._ended:
            return
        self._ended = True
        # No dedicated "complete" endpoint; the trace is already created.

    # -- public --------------------------------------------------------------

    @property
    def id(self) -> str:
        return self._trace_id

    @contextmanager
    def span(
        self,
        name: str,
        *,
        type: str = "span",
        parent_span_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[_SpanContext, None, None]:
        """Create a span under this trace as a context manager."""
        span_id = str(uuid.uuid4())
        span_kwargs: dict[str, Any] = {}
        if parent_span_id:
            span_kwargs["parentObservationId"] = parent_span_id
        if "input" in kwargs:
            span_kwargs["input"] = kwargs.pop("input")
        if "model" in kwargs:
            span_kwargs["model"] = kwargs.pop("model")

        self._client.create_span(
            self._trace_id,
            name,
            type=type,
            id=span_id,
            **span_kwargs,
        )

        ctx = _SpanContext(client=self._client, trace_id=self._trace_id, span_id=span_id)
        ctx._start_time = time.time()
        yield ctx
        ctx._end()

    def score(self, name: str, value: float, comment: Optional[str] = None) -> None:
        """Shorthand to add a score to this trace."""
        self._client.create_score(self._trace_id, name, value, comment=comment)


class _SpanContext:
    """Returned by ``_TraceContext.span()`` context manager."""

    def __init__(self, client: AgentDevInsightClient, trace_id: str, span_id: str):
        self._client = client
        self._trace_id = trace_id
        self._span_id = span_id
        self._start_time: float = 0.0
        self._ended = False

    @property
    def id(self) -> str:
        return self._span_id

    def _end(self, output: Optional[dict[str, Any]] = None, error: Optional[str] = None) -> None:
        if self._ended:
            return
        self._ended = True
        end_kwargs: dict[str, Any] = {}
        if output is not None:
            end_kwargs["output"] = output
        if error:
            end_kwargs["statusMessage"] = error
        # The spans endpoint supports upsert by id; send end info.
        self._client.create_span(
            self._trace_id,
            name="",  # name is required by the API schema
            id=self._span_id,
            **end_kwargs,
        )

    def generation(
        self,
        *,
        model: str,
        prompt: Any | None = None,
        completion: Any | None = None,
        usage: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record an LLM generation under this span."""
        meta: dict[str, Any] = {}
        if self._start_time:
            meta["latency_ms"] = round((time.time() - self._start_time) * 1000, 2)
        self._client.create_generation(
            self._span_id,
            model=model,
            prompt=prompt,
            completion=completion,
            usage=usage,
            metadata=meta or None,
        )


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_global_client: Optional[AgentDevInsightClient] = None


def get_client(**kwargs: Any) -> AgentDevInsightClient:
    """Return a module-level singleton ``AgentDevInsightClient``."""
    global _global_client
    if _global_client is None:
        _global_client = AgentDevInsightClient(**kwargs)
    return _global_client
