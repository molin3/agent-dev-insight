"""评估器、数据集、实验 集成测试"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dataset_service import DatasetService
from app.services.evaluation_service import BUILTIN_EVALUATORS, EvaluationService
from app.services.experiment_service import ExperimentService
from app.services.trace_service import TraceService


# ============================
# 评估器测试
# ============================

@pytest.mark.asyncio
async def test_evaluator_registry():
    from app.evaluators.registry import EvaluatorRegistry

    all_eval = EvaluatorRegistry.get_all()
    for name in BUILTIN_EVALUATORS:
        assert name in all_eval, f"Evaluator {name} should be registered"
        evaluator = EvaluatorRegistry.create(name)
        assert evaluator is not None


@pytest.mark.asyncio
async def test_run_evaluators_on_trace(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="eval-test")
    span = await service.create_span(trace_id=trace.id, name="llm", type="llm")
    await service.create_generation(
        span_id=span.id,
        model="deepseek-chat",
        completion="test output",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )
    await service.create_span(
        trace_id=trace.id, name="search", type="tool"
    )
    await service.complete_trace(trace.id)

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(trace.id)

    assert len(scores) > 0
    score_names = [s.name for s in scores]
    assert "completion_rate" in score_names
    assert "total_tokens" in score_names


@pytest.mark.asyncio
async def test_evaluate_trace_via_api(client: AsyncClient, db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="api-eval")
    span = await service.create_span(trace_id=trace.id, name="llm", type="llm")
    await service.create_generation(
        span_id=span.id,
        model="deepseek-chat",
        completion="result",
        usage={"total_tokens": 10},
    )
    await service.complete_trace(trace.id)

    response = await client.post(f"/api/traces/{trace.id}/evaluate", json={
        "evaluator_names": ["completion_rate", "token_cost"],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["score_count"] >= 3  # completion_rate + total_tokens + total_cost


@pytest.mark.asyncio
async def test_list_evaluators(client: AsyncClient):
    response = await client.get("/api/evaluators")
    assert response.status_code == 200
    data = response.json()
    assert "builtin" in data["data"]
    assert len(data["data"]["builtin"]) >= 5


@pytest.mark.asyncio
async def test_dashboard_overview(client: AsyncClient, db_session: AsyncSession):
    service = TraceService(db_session)
    await service.create_trace(project_id="p1", name="dash-1")
    await service.create_trace(project_id="p1", name="dash-2")

    response = await client.get("/api/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total_traces"] == 2


# ============================
# 数据集测试
# ============================

@pytest.mark.asyncio
async def test_create_dataset(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds = await service.create_dataset(name="test-ds", description="test")
    assert ds.name == "test-ds"
    assert ds.version == 1


@pytest.mark.asyncio
async def test_add_item_to_dataset(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds = await service.create_dataset(name="ds1")
    item = await service.add_item(
        dataset_id=ds.id,
        input={"query": "hello"},
        expected_output="world",
    )
    assert item.input == {"query": "hello"}


@pytest.mark.asyncio
async def test_create_item_from_trace(db_session: AsyncSession):
    ds_service = DatasetService(db_session)
    trace_service = TraceService(db_session)

    ds = await ds_service.create_dataset(name="from-trace")
    trace = await trace_service.create_trace(project_id="p1", name="src")
    span = await trace_service.create_span(trace_id=trace.id, name="llm", type="llm")
    await trace_service.create_generation(
        span_id=span.id, model="d", completion="generated text"
    )

    item = await ds_service.create_item_from_trace(ds.id, trace.id)
    assert item is not None
    assert item.source_trace_id == trace.id


@pytest.mark.asyncio
async def test_dataset_via_api(client: AsyncClient):
    response = await client.post("/api/datasets", json={
        "name": "api-dataset",
    })
    assert response.status_code == 201
    data = response.json()
    ds_id = data["data"]["id"]

    response = await client.post(f"/api/datasets/{ds_id}/items", json={
        "input": {"q": "test"},
        "expected_output": "answer",
    })
    assert response.status_code == 201

    response = await client.get(f"/api/datasets/{ds_id}")
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 1


# ============================
# 实验测试
# ============================

@pytest.mark.asyncio
async def test_create_experiment(db_session: AsyncSession):
    service = ExperimentService(db_session)
    exp = await service.create_experiment(
        name="model-compare",
        task_description="Compare models on translation task",
    )
    assert exp.name == "model-compare"
    assert exp.status == "pending"


@pytest.mark.asyncio
async def test_add_run_to_experiment(db_session: AsyncSession):
    service = ExperimentService(db_session)
    exp = await service.create_experiment(name="e1", task_description="test")
    run = await service.add_run(
        experiment_id=exp.id,
        model_name="deepseek-chat",
        provider="deepseek",
    )
    assert run.model_name == "deepseek-chat"

    await service.complete_run(
        run_id=run.id,
        avg_latency_ms=1234.0,
        total_tokens=500,
        total_cost=0.05,
        completion_rate=0.95,
    )

    comparison = await service.get_comparison_data(exp.id)
    assert "deepseek-chat" in comparison["models"]


@pytest.mark.asyncio
async def test_experiment_via_api(client: AsyncClient):
    response = await client.post("/api/experiments", json={
        "name": "api-experiment",
        "task_description": "Test task",
    })
    assert response.status_code == 201
    data = response.json()
    exp_id = data["data"]["id"]

    response = await client.get(f"/api/experiments/{exp_id}")
    assert response.status_code == 200
    assert response.json()["data"]["experiment"]["name"] == "api-experiment"

    response = await client.get("/api/experiments?page=1&page_size=5")
    assert response.status_code == 200


# ============================
# Score API 测试
# ============================

@pytest.mark.asyncio
async def test_get_trace_scores_via_api(client: AsyncClient, db_session: AsyncSession):
    from app.services.score_service import ScoreService

    trace_service = TraceService(db_session)
    trace = await trace_service.create_trace(project_id="p1", name="score-test")

    score_service = ScoreService(db_session)
    await score_service.create_score(trace_id=trace.id, name="test_score", value=0.88)

    response = await client.get(f"/api/traces/{trace.id}/scores")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["scores"]) == 1
    assert data["data"]["scores"][0]["value"] == 0.88


@pytest.mark.asyncio
async def test_score_via_public_api(client: AsyncClient, db_session: AsyncSession):
    trace_service = TraceService(db_session)
    trace = await trace_service.create_trace(project_id="p1", name="pub-score")

    response = await client.post("/api/public/scores", json={
        "traceId": trace.id,
        "name": "accuracy",
        "value": 0.92,
        "comment": "via public API",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["id"] is not None
