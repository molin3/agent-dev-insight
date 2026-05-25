"""SDK 类型定义"""

from typing import Optional

from pydantic import BaseModel


class TraceInfo(BaseModel):
    id: str
    name: str
    project_id: str = "default"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict] = None


class SpanInfo(BaseModel):
    id: str
    trace_id: str
    name: str
    type: str = "span"
    parent_span_id: Optional[str] = None
    input: Optional[dict] = None
    output: Optional[dict] = None
    model: Optional[str] = None


class GenerationInfo(BaseModel):
    span_id: str
    model: str
    prompt: Optional[list] = None
    completion: Optional[str] = None
    usage: Optional[dict] = None
    cost: Optional[float] = None
    latency_ms: Optional[float] = None
