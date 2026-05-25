"""Trace / Span / Generation 三级层级模型"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.score import Score


class Trace(BaseModel):
    __tablename__ = "traces"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress", index=True
    )
    release: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="traces")
    spans: Mapped[list["Span"]] = relationship(
        "Span", back_populates="trace", cascade="all, delete-orphan", order_by="Span.started_at"
    )
    scores: Mapped[list["Score"]] = relationship(
        "Score", back_populates="trace", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_traces_project_timestamp", "project_id", "started_at"),
        Index("ix_traces_session", "session_id"),
    )


class Span(BaseModel):
    __tablename__ = "spans"

    trace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_span_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("spans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="span"
    )  # llm | tool | retriever | embedding | agent | custom
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    usage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0)

    trace: Mapped["Trace"] = relationship(back_populates="spans")
    parent_span: Mapped[Optional["Span"]] = relationship(
        "Span", remote_side="Span.id", back_populates="child_spans"
    )
    child_spans: Mapped[list["Span"]] = relationship(
        "Span", back_populates="parent_span", cascade="all, delete-orphan"
    )
    generations: Mapped[list["Generation"]] = relationship(
        "Generation", back_populates="span", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_spans_trace_type", "trace_id", "type"),
        Index("ix_spans_parent", "parent_span_id"),
        Index("ix_spans_started", "started_at"),
    )


class Generation(BaseModel):
    __tablename__ = "generations"

    span_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("spans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    completion: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    span: Mapped["Span"] = relationship(back_populates="generations")
