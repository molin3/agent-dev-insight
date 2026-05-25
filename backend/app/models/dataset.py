"""Dataset / DatasetItem / DatasetRun 模型"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Dataset(BaseModel):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    items: Mapped[list["DatasetItem"]] = relationship(
        "DatasetItem", back_populates="dataset", cascade="all, delete-orphan"
    )
    runs: Mapped[list["DatasetRun"]] = relationship(
        "DatasetRun", back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetItem(BaseModel):
    __tablename__ = "dataset_items"

    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input: Mapped[dict] = mapped_column(JSON, nullable=False)
    expected_output: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    eval_criteria: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source_trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="items")


class DatasetRun(BaseModel):
    __tablename__ = "dataset_runs"

    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    passed_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    git_commit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trace_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="runs")
