"""``@trace`` decorator for wrapping functions in AgentDevInsight traces."""

from __future__ import annotations

import logging
import time
import traceback
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from .client import AgentDevInsightClient, get_client

logger = logging.getLogger("agentdevinsight.decorators")

F = TypeVar("F", bound=Callable[..., Any])


def trace(
    *,
    name: str | None = None,
    client: AgentDevInsightClient | None = None,
    capture_args: bool = True,
    capture_result: bool = True,
) -> Callable[[F], F]:
    """Decorator that wraps a function execution in an AgentDevInsight trace.

    - Creates a trace before the call and records ``input``/``output`` as
      metadata.
    - Measures wall-clock execution time (``latency_ms``).
    - If the wrapped function raises, the trace is annotated with the error
      message and re-raised.

    Parameters
    ----------
    name : str, optional
        Trace name.  Defaults to the decorated function's ``__name__``.
    client : AgentDevInsightClient, optional
        Explicit client instance.  When omitted the module-level singleton
        returned by :func:`get_client` is used.
    capture_args : bool
        If *True*, function arguments are stored in the trace metadata under
        ``"input"``.  Defaults to *True*.
    capture_result : bool
        If *True*, the return value is stored in the trace metadata under
        ``"output"``.  Defaults to *True*.

    Usage::

        from agentdevinsight import trace

        @trace(name="my_agent")
        def my_agent(query: str) -> str:
            return call_llm(query)
    """

    def decorator(func: F) -> F:
        trace_name = name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            c = client or get_client()
            start = time.time()
            metadata: dict[str, Any] = {}
            if capture_args:
                metadata["input"] = _safe_repr({"args": args, "kwargs": kwargs})

            trace_resp = c.create_trace(trace_name, metadata=metadata)
            trace_id: str | None = None
            if trace_resp and "data" in trace_resp:
                trace_id = trace_resp["data"].get("id")

            try:
                result = func(*args, **kwargs)
                elapsed_ms = round((time.time() - start) * 1000, 2)
                if capture_result:
                    metadata["output"] = _safe_repr(result)
                metadata["latency_ms"] = elapsed_ms
                metadata["status"] = "success"
                # Update trace with output metadata
                if trace_id:
                    c.create_trace(trace_name, id=trace_id, metadata=metadata)
                return result
            except Exception as exc:
                elapsed_ms = round((time.time() - start) * 1000, 2)
                metadata["latency_ms"] = elapsed_ms
                metadata["status"] = "error"
                metadata["error"] = f"{type(exc).__name__}: {exc}"
                metadata["traceback"] = traceback.format_exc()
                if trace_id:
                    c.create_trace(trace_name, id=trace_id, metadata=metadata)
                raise

        return cast(F, wrapper)

    return decorator


def _safe_repr(obj: Any, max_len: int = 2000) -> Any:
    """Return a JSON-serialisable, length-capped representation of *obj*."""
    try:
        import json
        text = json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        text = repr(obj)
    if len(text) > max_len:
        return text[:max_len] + "..."
    # Round-trip back to a Python object so the caller stores native types
    try:
        import json
        return json.loads(text)
    except Exception:
        return text
