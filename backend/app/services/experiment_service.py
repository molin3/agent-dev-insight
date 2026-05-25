"""Experiment 服务 — 模型对比实验管理"""

import logging
import random

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.experiment import ComparisonResult, Experiment, ExperimentRun
from app.utils.helpers import gen_uuid

logger = logging.getLogger(__name__)

# 模拟的模型配置：名称、提供商、典型延迟范围(ms)、Token范围、成本($)
SIMULATED_MODELS = [
    ("deepseek-chat", "deepseek", (400, 1200), (100, 500), (0.0001, 0.001)),
    ("gpt-4o", "openai", (800, 2500), (80, 400), (0.50, 3.00)),
    ("claude-3.5-sonnet", "anthropic", (600, 2000), (120, 450), (1.00, 5.00)),
    ("qwen-max", "alibaba", (500, 1800), (90, 420), (0.10, 1.00)),
]


class ExperimentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_experiment(
        self,
        name: str,
        task_description: str,
        description: str | None = None,
        dataset_id: str | None = None,
    ) -> Experiment:
        exp = Experiment(
            id=gen_uuid(),
            name=name,
            description=description,
            task_description=task_description,
            dataset_id=dataset_id,
        )
        self.db.add(exp)
        await self.db.commit()
        await self.db.refresh(exp)
        return exp

    async def run_experiment(self, experiment_id: str) -> Experiment | None:
        """执行实验：为每个模拟模型创建 Run 并生成对比数据"""
        exp = await self.get_experiment(experiment_id)
        if exp is None:
            return None

        if exp.status == "running":
            return exp

        exp.status = "running"
        await self.db.commit()

        try:
            for model_name, provider, lat_range, tok_range, cost_range in SIMULATED_MODELS:
                # 创建 Run
                run = await self.add_run(
                    experiment_id=experiment_id,
                    model_name=model_name,
                    provider=provider,
                    config={"task": exp.task_description[:100]},
                )

                # 模拟执行结果
                latency = random.randint(*lat_range)
                tokens = random.randint(*tok_range)
                cost = round(random.uniform(*cost_range), 5)
                completion = round(random.uniform(0.75, 0.99), 2)

                await self.complete_run(
                    run_id=run.id,
                    avg_latency_ms=float(latency),
                    total_tokens=tokens,
                    total_cost=cost,
                    completion_rate=completion,
                )
                logger.info("Experiment run completed: %s / %s (rate=%.2f, cost=$%.4f)",
                            experiment_id, model_name, completion, cost)

            # 生成对比结果
            runs = await self._get_runs(experiment_id)
            model_names = [r.model_name for r in runs]
            for i in range(len(model_names)):
                for j in range(i + 1, len(model_names)):
                    a, b = model_names[i], model_names[j]
                    ra = next(r for r in runs if r.model_name == a)
                    rb = next(r for r in runs if r.model_name == b)

                    # 延迟越低越好
                    winner = None
                    if ra.completion_rate and rb.completion_rate:
                        diff = ra.completion_rate - rb.completion_rate
                        if abs(diff) > 0.03:
                            winner = "a" if diff > 0 else "b"

                    self.db.add(ComparisonResult(
                        id=gen_uuid(),
                        experiment_id=experiment_id,
                        model_a=a,
                        model_b=b,
                        metric="completion_rate",
                        value_a=ra.completion_rate or 0,
                        value_b=rb.completion_rate or 0,
                        winner=winner,
                    ))
            await self.db.commit()

            exp.status = "completed"
            await self.db.commit()
            await self.db.refresh(exp)
            logger.info("Experiment completed: %s with %d models", experiment_id, len(model_names))

        except Exception as e:
            logger.error("Experiment failed: %s", e)
            exp.status = "failed"
            await self.db.commit()

        return exp

    async def _get_runs(self, experiment_id: str) -> list[ExperimentRun]:
        result = await self.db.execute(
            select(ExperimentRun).where(ExperimentRun.experiment_id == experiment_id)
        )
        return list(result.scalars().all())

    async def get_experiment(self, experiment_id: str) -> Experiment | None:
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.runs))
            .where(Experiment.id == experiment_id)
        )
        return result.scalar_one_or_none()

    async def get_experiments(self, page: int = 1, page_size: int = 20) -> dict:
        query = select(Experiment).order_by(Experiment.created_at.desc())
        count_query = select(func.count()).select_from(Experiment)
        total = (await self.db.execute(count_query)).scalar() or 0
        items = (
            await self.db.execute(query.offset((page - 1) * page_size).limit(page_size))
        ).scalars().all()
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    async def add_run(
        self,
        experiment_id: str,
        model_name: str,
        provider: str,
        config: dict | None = None,
    ) -> ExperimentRun:
        run = ExperimentRun(
            id=gen_uuid(),
            experiment_id=experiment_id,
            model_name=model_name,
            provider=provider,
            config=config,
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def complete_run(
        self,
        run_id: str,
        avg_latency_ms: float | None = None,
        total_tokens: int | None = None,
        total_cost: float | None = None,
        completion_rate: float | None = None,
        trace_id: str | None = None,
    ) -> ExperimentRun | None:
        result = await self.db.execute(select(ExperimentRun).where(ExperimentRun.id == run_id))
        run = result.scalar_one_or_none()
        if run is None:
            return None
        run.avg_latency_ms = avg_latency_ms
        run.total_tokens = total_tokens
        run.total_cost = total_cost
        run.completion_rate = completion_rate
        run.trace_id = trace_id
        run.status = "completed"
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get_comparison_data(self, experiment_id: str) -> dict:
        result = await self.db.execute(
            select(ExperimentRun).where(ExperimentRun.experiment_id == experiment_id)
        )
        runs = list(result.scalars().all())

        models = []
        metrics = {
            "avg_latency_ms": {},
            "total_tokens": {},
            "total_cost": {},
            "completion_rate": {},
        }

        for run in runs:
            models.append(run.model_name)
            metrics["avg_latency_ms"][run.model_name] = run.avg_latency_ms
            metrics["total_tokens"][run.model_name] = run.total_tokens
            metrics["total_cost"][run.model_name] = run.total_cost
            metrics["completion_rate"][run.model_name] = run.completion_rate

        return {"models": models, "metrics": metrics}

    async def delete_experiment(self, experiment_id: str) -> bool:
        exp = await self.get_experiment(experiment_id)
        if exp is None:
            return False
        await self.db.delete(exp)
        await self.db.commit()
        return True
