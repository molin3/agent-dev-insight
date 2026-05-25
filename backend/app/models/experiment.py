"""Experiment / ExperimentRun / ComparisonResult 模型"""

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Experiment(BaseModel):
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    dataset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("datasets.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")

    runs: Mapped[list["ExperimentRun"]] = relationship(
        "ExperimentRun", back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentRun(BaseModel):
    __tablename__ = "experiment_runs"

    experiment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    trace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("traces.id"), nullable=True
    )
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    experiment: Mapped["Experiment"] = relationship(back_populates="runs")
    trace = relationship("Trace")


class ComparisonResult(BaseModel):
    __tablename__ = "comparison_results"

    experiment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_a: Mapped[str] = mapped_column(String(100), nullable=False)
    model_b: Mapped[str] = mapped_column(String(100), nullable=False)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    value_a: Mapped[float] = mapped_column(Float, nullable=False)
    value_b: Mapped[float] = mapped_column(Float, nullable=False)
    winner: Mapped[str | None] = mapped_column(String(20), nullable=True)
