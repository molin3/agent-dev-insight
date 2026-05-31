"""Score 和 EvalConfig 模型"""

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Score(BaseModel):
    __tablename__ = "scores"

    trace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    span_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("spans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    config_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    trace = relationship("Trace", back_populates="scores")
    span = relationship("Span")


