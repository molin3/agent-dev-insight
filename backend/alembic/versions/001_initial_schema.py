"""initial schema

Revision ID: 001
Revises: None
Create Date: 2026-05-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Projects
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Traces
    op.create_table(
        "traces",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress", index=True),
        sa.Column("release", sa.String(100), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("total_latency_ms", sa.Float(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("total_cost", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_traces_project_timestamp", "traces", ["project_id", "started_at"])
    op.create_index("ix_traces_session", "traces", ["session_id"])

    # Spans
    op.create_table(
        "spans",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("trace_id", sa.String(36), sa.ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("parent_span_id", sa.String(36), sa.ForeignKey("spans.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(50), nullable=False, server_default="span"),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("input", sa.JSON(), nullable=True),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("usage", sa.JSON(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_spans_trace_type", "spans", ["trace_id", "type"])
    op.create_index("ix_spans_parent", "spans", ["parent_span_id"])
    op.create_index("ix_spans_started", "spans", ["started_at"])

    # Generations
    op.create_table(
        "generations",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("span_id", sa.String(36), sa.ForeignKey("spans.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt", sa.JSON(), nullable=True),
        sa.Column("completion", sa.Text(), nullable=True),
        sa.Column("usage", sa.JSON(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Scores
    op.create_table(
        "scores",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("trace_id", sa.String(36), sa.ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("span_id", sa.String(36), sa.ForeignKey("spans.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("comment", sa.String(1000), nullable=True),
        sa.Column("config_id", sa.String(36), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Eval Configs
    op.create_table(
        "eval_configs",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("prompt_template", sa.String(5000), nullable=False),
        sa.Column("target", sa.String(10), nullable=False, server_default="trace"),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Datasets
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Dataset Items
    op.create_table(
        "dataset_items",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("expected_output", sa.String(5000), nullable=True),
        sa.Column("eval_criteria", sa.String(2000), nullable=True),
        sa.Column("source_trace_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Dataset Runs
    op.create_table(
        "dataset_runs",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("total_items", sa.Integer(), server_default="0"),
        sa.Column("passed_items", sa.Integer(), server_default="0"),
        sa.Column("failed_items", sa.Integer(), server_default="0"),
        sa.Column("pass_rate", sa.Float(), nullable=True),
        sa.Column("previous_pass_rate", sa.Float(), nullable=True),
        sa.Column("git_commit", sa.String(40), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("trace_ids", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Experiments
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Experiment Runs
    op.create_table(
        "experiment_runs",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("trace_id", sa.String(36), sa.ForeignKey("traces.id"), nullable=True),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("total_cost", sa.Float(), nullable=True),
        sa.Column("completion_rate", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Comparison Results
    op.create_table(
        "comparison_results",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model_a", sa.String(100), nullable=False),
        sa.Column("model_b", sa.String(100), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("value_a", sa.Float(), nullable=False),
        sa.Column("value_b", sa.Float(), nullable=False),
        sa.Column("winner", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("comparison_results")
    op.drop_table("experiment_runs")
    op.drop_table("experiments")
    op.drop_table("dataset_runs")
    op.drop_table("dataset_items")
    op.drop_table("datasets")
    op.drop_table("eval_configs")
    op.drop_table("scores")
    op.drop_table("generations")
    op.drop_table("spans")
    op.drop_table("traces")
    op.drop_table("projects")
