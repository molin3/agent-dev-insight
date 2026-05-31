"""评估器单元测试"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trace_service import TraceService
from app.services.evaluation_service import EvaluationService, BUILTIN_EVALUATORS
from app.evaluators.builtin.completion_rate import CompletionRateEvaluator
from app.evaluators.builtin.latency import LatencyEvaluator
from app.evaluators.builtin.token_cost import TokenCostEvaluator
from app.evaluators.builtin.tool_accuracy import ToolAccuracyEvaluator
from app.evaluators.builtin.hallucination import HallucinationEvaluator
from app.evaluators.registry import EvaluatorRegistry


@pytest.mark.asyncio
async def test_completion_rate_completed_with_output(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(trace_id=trace.id, name="s1")
    await service.create_generation(
        span_id=span.id, model="test", prompt="hi", completion="hello"
    )
    await service.complete_trace(trace.id)
    await db_session.refresh(trace)

    spans = await service.get_spans_for_trace(trace.id)
    evaluator = CompletionRateEvaluator()
    scores = await evaluator.evaluate(trace, spans)
    assert len(scores) == 1
    assert scores[0].name == "completion_rate"
    assert scores[0].value == 0.95


@pytest.mark.asyncio
async def test_completion_rate_in_progress(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")

    evaluator = CompletionRateEvaluator()
    scores = await evaluator.evaluate(trace, [])
    assert len(scores) == 1
    assert scores[0].value == 0.5


@pytest.mark.asyncio
async def test_completion_rate_error(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    trace.status = "error"
    await db_session.commit()

    evaluator = CompletionRateEvaluator()
    scores = await evaluator.evaluate(trace, [])
    assert scores[0].value == 0.0


@pytest.mark.asyncio
async def test_latency_no_latencies_returns_empty(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")

    evaluator = LatencyEvaluator()
    scores = await evaluator.evaluate(trace, [])
    assert scores == []


@pytest.mark.asyncio
async def test_latency_with_spans(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(trace_id=trace.id, name="s1")
    span.latency_ms = 500.0
    await db_session.commit()

    spans = await service.get_spans_for_trace(trace.id)
    evaluator = LatencyEvaluator()
    scores = await evaluator.evaluate(trace, spans)
    assert len(scores) == 3  # p50, p95, p99
    names = {s.name for s in scores}
    assert names == {"latency_p50", "latency_p95", "latency_p99"}


@pytest.mark.asyncio
async def test_token_cost_no_generations(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    await service.create_span(trace_id=trace.id, name="s1")

    spans = await service.get_spans_for_trace(trace.id)
    evaluator = TokenCostEvaluator()
    scores = await evaluator.evaluate(trace, spans)
    assert len(scores) == 2
    assert all(s.value == 0.0 for s in scores)


@pytest.mark.asyncio
async def test_tool_accuracy_no_tools_returns_empty(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")

    evaluator = ToolAccuracyEvaluator()
    scores = await evaluator.evaluate(trace, [])
    assert scores == []


@pytest.mark.asyncio
async def test_hallucination_no_llm_returns_empty(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(trace_id=trace.id, name="s1", type="tool")

    evaluator = HallucinationEvaluator()
    scores = await evaluator.evaluate(trace, [span])
    assert scores == []


@pytest.mark.asyncio
async def test_evaluator_registry():
    names = list(EvaluatorRegistry.get_all().keys())
    for expected in BUILTIN_EVALUATORS:
        assert expected in names


@pytest.mark.asyncio
async def test_evaluator_registry_create():
    evaluator = EvaluatorRegistry.create("completion_rate")
    assert evaluator is not None
    assert isinstance(evaluator, CompletionRateEvaluator)

    unknown = EvaluatorRegistry.create("nonexistent")
    assert unknown is None


@pytest.mark.asyncio
async def test_evaluate_trace_via_service(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(trace_id=trace.id, name="s1")
    await service.create_generation(
        span_id=span.id, model="test", prompt="hi", completion="hello"
    )
    await service.complete_trace(trace.id)

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(trace.id)
    assert len(scores) >= 1
    score_names = {s.name for s in scores}
    assert "completion_rate" in score_names


@pytest.mark.asyncio
async def test_evaluate_trace_nonexistent(db_session: AsyncSession):
    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace("nonexistent-id")
    assert scores == []


@pytest.mark.asyncio
async def test_get_evaluator_list(db_session: AsyncSession):
    eval_service = EvaluationService(db_session)
    evaluator_list = await eval_service.get_evaluator_list()
    assert len(evaluator_list) == len(BUILTIN_EVALUATORS)
    names = [e["name"] for e in evaluator_list]
    for expected in BUILTIN_EVALUATORS:
        assert expected in names
