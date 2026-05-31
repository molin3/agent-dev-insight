"""Experiment 服务 — 真实 LLM 模型对比实验"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.llm_client import LLMClient, LLMResponse
from app.models.dataset import DatasetItem
from app.models.experiment import ComparisonResult, Experiment, ExperimentRun
from app.utils.helpers import gen_uuid

logger = logging.getLogger(__name__)

# 默认对比模型列表
DEFAULT_MODELS = [
    {"name": settings.llm_model, "provider": "openai-compatible"},
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

    async def run_experiment(
        self,
        experiment_id: str,
        model_names: list[str] | None = None,
    ) -> Experiment | None:
        """执行实验：对每个模型用 Dataset 用例执行真实 LLM 调用"""
        exp = await self.get_experiment(experiment_id)
        if exp is None:
            return None

        if exp.status == "running":
            return exp

        exp.status = "running"
        await self.db.commit()

        # 确定要对比的模型
        models = model_names or [m["name"] for m in DEFAULT_MODELS]

        # 获取测试用例
        test_cases = await self._get_test_cases(exp.dataset_id)
        if not test_cases:
            # 没有数据集时，用 task_description 作为单一测试用例
            test_cases = [{"input": exp.task_description, "expected_output": None}]

        try:
            for model_name in models:
                run = await self.add_run(
                    experiment_id=experiment_id,
                    model_name=model_name,
                    provider="openai-compatible",
                    config={"task": exp.task_description[:200]},
                )

                # 对每个测试用例执行 LLM 调用
                results = await self._run_test_cases(model_name, test_cases)

                # 聚合结果
                total_latency = sum(r.latency_ms for r in results)
                total_tokens = sum(r.total_tokens for r in results)
                avg_latency = total_latency / len(results) if results else 0

                # 估算成本（简化：使用 token 数量）
                completed_count = sum(1 for r in results if r.content)
                completion_rate = completed_count / len(results) if results else 0

                await self.complete_run(
                    run_id=run.id,
                    avg_latency_ms=avg_latency,
                    total_tokens=total_tokens,
                    total_cost=0.0,  # 需要模型定价表才能准确计算
                    completion_rate=completion_rate,
                )
                logger.info(
                    "Experiment run: %s / %s (latency=%.0fms, tokens=%d, rate=%.2f)",
                    experiment_id, model_name, avg_latency, total_tokens, completion_rate,
                )

            # 生成对比结果
            await self._generate_comparisons(experiment_id)

            exp.status = "completed"
            await self.db.commit()
            await self.db.refresh(exp)
            logger.info("Experiment completed: %s with %d models", experiment_id, len(models))

        except Exception as e:
            logger.error("Experiment failed: %s", e, exc_info=True)
            exp.status = "failed"
            await self.db.commit()

        return exp

    async def _get_test_cases(self, dataset_id: str | None) -> list[dict]:
        """从数据集获取测试用例"""
        if not dataset_id:
            return []

        result = await self.db.execute(
            select(DatasetItem)
            .where(DatasetItem.dataset_id == dataset_id)
            .order_by(DatasetItem.created_at)
            .limit(20)  # 限制最多 20 个用例，避免 API 调用过多
        )
        items = result.scalars().all()
        return [
            {"input": item.input, "expected_output": item.expected_output}
            for item in items
        ]

    async def _run_test_cases(
        self, model_name: str, test_cases: list[dict]
    ) -> list[LLMResponse]:
        """对一组测试用例执行 LLM 调用"""
        client = LLMClient(model=model_name)
        results = []
        for case in test_cases:
            input_text = (
                case["input"].get("query", str(case["input"]))
                if isinstance(case["input"], dict)
                else str(case["input"])
            )
            try:
                response = await client.chat(prompt=input_text)
                results.append(response)
            except Exception as e:
                logger.error("LLM call failed for model %s: %s", model_name, e)
                # 失败时记录空结果
                results.append(LLMResponse(
                    content="", model=model_name,
                    prompt_tokens=0, completion_tokens=0,
                    total_tokens=0, latency_ms=0,
                ))
        return results

    async def _generate_comparisons(self, experiment_id: str) -> None:
        """生成模型两两对比结果"""
        runs = await self._get_runs(experiment_id)
        model_names = [r.model_name for r in runs]
        metrics = ["avg_latency_ms", "total_tokens", "completion_rate"]

        for i in range(len(model_names)):
            for j in range(i + 1, len(model_names)):
                a, b = model_names[i], model_names[j]
                ra = next(r for r in runs if r.model_name == a)
                rb = next(r for r in runs if r.model_name == b)

                for metric in metrics:
                    va = getattr(ra, metric) or 0
                    vb = getattr(rb, metric) or 0

                    winner = None
                    if va != vb:
                        # 延迟和 token 越低越好，完成率越高越好
                        if metric in ("avg_latency_ms", "total_tokens"):
                            winner = "a" if va < vb else "b"
                        else:
                            winner = "a" if va > vb else "b"

                    self.db.add(ComparisonResult(
                        id=gen_uuid(),
                        experiment_id=experiment_id,
                        model_a=a,
                        model_b=b,
                        metric=metric,
                        value_a=va,
                        value_b=vb,
                        winner=winner,
                    ))
        await self.db.commit()

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

    async def update_experiment(self, experiment_id: str, **kwargs) -> Experiment | None:
        exp = await self.get_experiment(experiment_id)
        if exp is None:
            return None
        for key, value in kwargs.items():
            if key in ("name", "description") and value is not None:
                setattr(exp, key, value)
        await self.db.commit()
        await self.db.refresh(exp)
        return exp

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
