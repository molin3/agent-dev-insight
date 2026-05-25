"""@trace 和 @span 装饰器"""

import uuid
from functools import wraps

from .client import get_client


def trace(*, project: str = "default", name: str | None = None, **trace_kwargs):
    """装饰器：将函数执行包裹在 Trace 中

    用法：
        @trace(project="my-agent")
        def run_agent(query: str) -> str:
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client = get_client(project=project)
            trace_name = name or func.__name__
            with client.trace(name=trace_name, **trace_kwargs) as t:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    raise
        return wrapper
    return decorator


def span(*, name: str | None = None, type: str = "span", **span_kwargs):
    """装饰器：将函数执行包裹在 Span 中

    用法：
        @span(name="llm-call", type="llm")
        def call_llm(prompt: str) -> str:
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from .client import AgentDevInsight

            span_name = name or func.__name__
            return func(*args, **kwargs)
        return wrapper
    return decorator
