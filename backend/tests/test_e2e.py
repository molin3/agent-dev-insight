"""端到端集成测试 — 模拟完整 Agent 运行 → 评估流程"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.evaluation_service import EvaluationService
from app.services.score_service import ScoreService
from app.services.trace_service import TraceService


@pytest.mark.asyncio
async def test_full_agent_lifecycle(db_session: AsyncSession):
    """模拟完整流程：创建 Trace → 上报 Span/Generation → 完成 → 评估"""
    service = TraceService(db_session)

    # 1. 创建 Trace（模拟 Agent 开始运行）
    trace = await service.create_trace(
        project_id="demo-agent",
        name="search-summarize",
        tags=["demo", "e2e"],
    )
    assert trace.status == "in_progress"

    # 2. 上报 LLM Span + Generation（模拟规划步骤）
    llm_span = await service.create_span(
        trace_id=trace.id,
        name="plan-task",
        type="agent",
    )
    await service.create_generation(
        span_id=llm_span.id,
        model="deepseek-chat",
        prompt=[{"role": "user", "content": "Plan the task"}],
        completion="Step 1: Search. Step 2: Summarize.",
        usage={"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35},
    )
    await service.complete_span(llm_span.id, output={"plan": "search then summarize"})

    # 3. 上报 Tool Span + Generation（模拟搜索工具调用）
    tool_span = await service.create_span(
        trace_id=trace.id,
        name="web-search",
        type="tool",
    )
    await service.create_generation(
        span_id=tool_span.id,
        model="tavily-search",
        completion="Search result: AI news headlines",
        usage={"prompt_tokens": 5, "completion_tokens": 20, "total_tokens": 25},
    )
    await service.complete_span(tool_span.id, output={"results": ["news1", "news2"]})

    # 4. 上报第二个 LLM Span（模拟总结步骤）
    summarize_span = await service.create_span(
        trace_id=trace.id,
        name="llm-summarize",
        type="llm",
    )
    await service.create_generation(
        span_id=summarize_span.id,
        model="deepseek-chat",
        prompt=[{"role": "user", "content": "Summarize the search results"}],
        completion="Here is a summary of the latest AI news...",
        usage={"prompt_tokens": 30, "completion_tokens": 25, "total_tokens": 55},
    )
    await service.complete_span(summarize_span.id)

    # 5. 完成 Trace
    completed = await service.complete_trace(trace.id)
    assert completed.status == "completed"
    assert completed.total_tokens == 115  # 35 + 25 + 55
    assert completed.total_latency_ms is not None

    # 6. 运行评估
    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(trace.id)
    assert len(scores) > 0

    # 验证关键评分
    score_names = [s.name for s in scores]
    assert "completion_rate" in score_names
    assert "tool_accuracy" in score_names
    assert "total_tokens" in score_names
    assert "total_cost" in score_names

    # 验证分数值范围
    for s in scores:
        assert 0.0 <= s.value

    # 7. 验证数据完整性
    fetched = await service.get_trace(trace.id)
    assert fetched is not None
    assert len(fetched.spans) == 3
    assert fetched.total_tokens == 115

    # 8. 验证 replay
    events = await service.get_trace_replay(trace.id)
    assert len(events) >= 3  # at least span events


@pytest.mark.asyncio
async def test_e2e_via_api(client: AsyncClient, db_session: AsyncSession):
    """通过完整 API 调用链路模拟"""
    from app.models.project import Project

    # 创建项目
    proj = Project(id="demo-proj", name="demo-agent")
    db_session.add(proj)
    await db_session.commit()

    # 1. 创建 Trace
    resp = await client.post("/api/public/traces", json={
        "name": "api-e2e-test",
        "projectId": "demo-proj",
        "tags": ["e2e"],
    })
    assert resp.status_code == 201
    trace_id = resp.json()["data"]["id"]

    # 2. 创建 Span
    resp = await client.post("/api/public/spans", json={
        "traceId": trace_id,
        "name": "llm-call",
        "type": "llm",
        "model": "deepseek-chat",
    })
    assert resp.status_code == 201
    span_id = resp.json()["data"]["id"]

    # 3. 创建 Generation
    resp = await client.post("/api/public/generations", json={
        "spanId": span_id,
        "model": "deepseek-chat",
        "input": [{"role": "user", "content": "hello"}],
        "output": "world",
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    })
    assert resp.status_code == 201

    # 4. 完成 Trace
    resp = await client.post(f"/api/traces/{trace_id}/complete")
    assert resp.status_code == 200

    # 5. 评估
    resp = await client.post(f"/api/traces/{trace_id}/evaluate")
    assert resp.status_code == 200
    eval_data = resp.json()
    assert eval_data["data"]["score_count"] >= 3

    # 6. 获取评分
    resp = await client.get(f"/api/traces/{trace_id}/scores")
    assert resp.status_code == 200
    scores_data = resp.json()
    assert len(scores_data["data"]["scores"]) >= 3

    # 7. Dashboard 数据应包含此 Trace
    resp = await client.get("/api/dashboard/overview")
    assert resp.status_code == 200
    assert resp.json()["data"]["total_traces"] >= 1


@pytest.mark.asyncio
async def test_dataset_regression_flow(db_session: AsyncSession):
    """测试数据集回归测试完整流程"""
    from app.services.dataset_service import DatasetService

    trace_service = TraceService(db_session)
    ds_service = DatasetService(db_session)

    # 1. 创建数据集
    ds = await ds_service.create_dataset(name="regression-test-ds")

    # 2. 创建测试 Trace
    trace = await trace_service.create_trace(project_id="p1", name="regression-src")
    span = await trace_service.create_span(trace_id=trace.id, name="llm", type="llm")
    await trace_service.create_generation(
        span_id=span.id, model="d", completion="expected answer"
    )

    # 3. 从 Trace 创建数据集条目
    item = await ds_service.create_item_from_trace(ds.id, trace.id)
    assert item is not None
    assert item.source_trace_id == trace.id

    # 4. 创建 DatasetRun
    run = await ds_service.create_run(ds.id)
    assert run.status == "pending"

    # 5. 完成 Run
    completed_run = await ds_service.complete_run(run.id, passed=8, failed=2)
    assert completed_run.status == "completed"
    assert completed_run.pass_rate == 0.8


@pytest.mark.asyncio
async def test_experiment_comparison_flow(db_session: AsyncSession):
    """测试模型对比实验完整流程"""
    from app.services.experiment_service import ExperimentService

    service = ExperimentService(db_session)

    # 1. 创建实验
    exp = await service.create_experiment(
        name="model-shootout",
        task_description="Compare DeepSeek vs GPT-4o on summarization",
    )

    # 2. 添加 Run
    for model, provider, latency, tokens, cost, rate in [
        ("deepseek-chat", "deepseek", 800.0, 200, 0.03, 0.92),
        ("gpt-4o", "openai", 1200.0, 180, 2.50, 0.95),
        ("claude-3.5-sonnet", "anthropic", 1500.0, 220, 6.00, 0.88),
    ]:
        run = await service.add_run(
            experiment_id=exp.id,
            model_name=model,
            provider=provider,
        )
        await service.complete_run(
            run_id=run.id,
            avg_latency_ms=latency,
            total_tokens=tokens,
            total_cost=cost,
            completion_rate=rate,
        )

    # 3. 获取对比数据
    comparison = await service.get_comparison_data(exp.id)
    assert len(comparison["models"]) == 3
    assert "deepseek-chat" in comparison["models"]
    assert "gpt-4o" in comparison["models"]
    assert comparison["metrics"]["completion_rate"]["deepseek-chat"] == 0.92
    assert comparison["metrics"]["total_cost"]["gpt-4o"] == 2.50
