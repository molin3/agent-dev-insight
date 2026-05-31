"""Experiment 服务测试"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.experiment_service import ExperimentService


@pytest.mark.asyncio
async def test_create_experiment(db_session: AsyncSession):
    service = ExperimentService(db_session)
    exp = await service.create_experiment(
        name="test-exp", task_description="Compare models", description="A test"
    )
    assert exp.id is not None
    assert exp.name == "test-exp"
    assert exp.status == "pending"


@pytest.mark.asyncio
async def test_get_experiment(db_session: AsyncSession):
    service = ExperimentService(db_session)
    created = await service.create_experiment(name="exp-1", task_description="task")
    fetched = await service.get_experiment(created.id)
    assert fetched is not None
    assert fetched.name == "exp-1"


@pytest.mark.asyncio
async def test_get_experiments_pagination(db_session: AsyncSession):
    service = ExperimentService(db_session)
    for i in range(4):
        await service.create_experiment(name=f"exp-{i}", task_description=f"task-{i}")

    result = await service.get_experiments(page=1, page_size=2)
    assert result["total"] == 4
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_run_experiment(db_session: AsyncSession):
    """实验执行：即使 LLM 调用失败（无有效 key），也应完成并记录 runs"""
    service = ExperimentService(db_session)
    exp = await service.create_experiment(name="run-exp", task_description="test task")
    result = await service.run_experiment(exp.id)
    assert result is not None
    # 实验应完成（即使 LLM 调用失败也会完成，只是内容为空）
    assert result.status in ("completed", "failed")

    runs = await service._get_runs(exp.id)
    assert len(runs) >= 1  # 至少有 1 个 model run


@pytest.mark.asyncio
async def test_run_experiment_with_models(db_session: AsyncSession):
    """指定多个模型执行实验"""
    service = ExperimentService(db_session)
    exp = await service.create_experiment(name="multi-model", task_description="test")
    result = await service.run_experiment(
        exp.id, model_names=["model-a", "model-b"]
    )
    assert result is not None

    runs = await service._get_runs(exp.id)
    assert len(runs) == 2
    model_names = {r.model_name for r in runs}
    assert model_names == {"model-a", "model-b"}


@pytest.mark.asyncio
async def test_run_experiment_already_running(db_session: AsyncSession):
    service = ExperimentService(db_session)
    exp = await service.create_experiment(name="running-exp", task_description="task")
    exp.status = "running"
    await db_session.commit()

    result = await service.run_experiment(exp.id)
    assert result.status == "running"


@pytest.mark.asyncio
async def test_run_experiment_with_dataset(db_session: AsyncSession):
    """使用数据集作为测试用例"""
    from app.services.dataset_service import DatasetService

    ds_service = DatasetService(db_session)
    ds = await ds_service.create_dataset(name="test-ds")
    await ds_service.add_item(ds.id, input={"query": "Hello, what is 1+1?"})
    await ds_service.add_item(ds.id, input={"query": "What is the capital of France?"})

    exp_service = ExperimentService(db_session)
    exp = await exp_service.create_experiment(
        name="ds-exp", task_description="math", dataset_id=ds.id
    )
    result = await exp_service.run_experiment(exp.id)
    assert result is not None
    assert result.status in ("completed", "failed")


@pytest.mark.asyncio
async def test_update_experiment(db_session: AsyncSession):
    service = ExperimentService(db_session)
    exp = await service.create_experiment(name="old-name", task_description="task")
    updated = await service.update_experiment(exp.id, name="new-name")
    assert updated is not None
    assert updated.name == "new-name"


@pytest.mark.asyncio
async def test_update_experiment_not_found(db_session: AsyncSession):
    service = ExperimentService(db_session)
    result = await service.update_experiment("nonexistent", name="x")
    assert result is None


@pytest.mark.asyncio
async def test_delete_experiment(db_session: AsyncSession):
    service = ExperimentService(db_session)
    exp = await service.create_experiment(name="to-delete", task_description="task")
    deleted = await service.delete_experiment(exp.id)
    assert deleted is True
    assert await service.get_experiment(exp.id) is None


@pytest.mark.asyncio
async def test_delete_experiment_not_found(db_session: AsyncSession):
    service = ExperimentService(db_session)
    deleted = await service.delete_experiment("nonexistent")
    assert deleted is False


@pytest.mark.asyncio
async def test_get_comparison_data(db_session: AsyncSession):
    service = ExperimentService(db_session)
    exp = await service.create_experiment(
        name="comp-exp", task_description="task",
        dataset_id=None,
    )
    await service.run_experiment(exp.id, model_names=["m1", "m2"])

    comparison = await service.get_comparison_data(exp.id)
    assert "models" in comparison
    assert "metrics" in comparison
    assert len(comparison["models"]) == 2
    assert "avg_latency_ms" in comparison["metrics"]
    assert "completion_rate" in comparison["metrics"]
