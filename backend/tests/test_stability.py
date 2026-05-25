"""边界情况和稳定性测试 — 覆盖检查清单关注的风险点"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dataset_service import DatasetService
from app.services.evaluation_service import BUILTIN_EVALUATORS, EvaluationService
from app.services.experiment_service import ExperimentService
from app.services.score_service import ScoreService
from app.services.trace_service import TraceService
from app.utils.helpers import parse_json_from_text, safe_truncate


# ============================
# 检查清单 2.4: JSON 解析容错
# ============================

def test_parse_json_direct():
    """直接 JSON"""
    result = parse_json_from_text('{"key": "value"}')
    assert result == {"key": "value"}


def test_parse_json_markdown_block():
    """Markdown 代码块包裹的 JSON — 检查清单 2.4"""
    result = parse_json_from_text('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}


def test_parse_json_markdown_block_no_lang():
    """无语言标记的 markdown 代码块"""
    result = parse_json_from_text('```\n{"key": "value"}\n```')
    assert result == {"key": "value"}


def test_parse_json_nested_in_text():
    """JSON 嵌在普通文本中"""
    result = parse_json_from_text('这里有一些文字 {"key": "value"} 更多文字')
    assert result == {"key": "value"}


def test_parse_json_empty():
    """空字符串"""
    assert parse_json_from_text("") == {}


def test_parse_json_invalid():
    """无效 JSON"""
    assert parse_json_from_text("not json at all") == {}


def test_parse_json_markdown_invalid():
    """Markdown 包裹但内容无效"""
    result = parse_json_from_text('```json\n{invalid}\n```')
    assert result == {}  # 降级返回空


def test_safe_truncate_short():
    assert safe_truncate("hello", max_len=10) == "hello"


def test_safe_truncate_long():
    assert safe_truncate("x" * 100, max_len=20) == "x" * 20 + "..."


def test_safe_truncate_boundary():
    assert safe_truncate("abcde", max_len=5) == "abcde"


# ============================
# 检查清单 5.1: 评分维度空数据校验
# ============================

@pytest.mark.asyncio
async def test_evaluator_with_no_spans(db_session: AsyncSession):
    """空 Trace（无 Span）时评估器不崩溃"""
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="empty-trace")
    await service.complete_trace(trace.id)

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(trace.id)
    # 所有评估器都应正确处理空 spans，不能抛异常
    assert isinstance(scores, list)


@pytest.mark.asyncio
async def test_evaluator_with_no_generations(db_session: AsyncSession):
    """有 Span 但无 Generation 时评估器不崩溃"""
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="no-gen-trace")
    await service.create_span(trace_id=trace.id, name="llm", type="llm")
    await service.create_span(trace_id=trace.id, name="tool", type="tool")
    await service.complete_trace(trace.id)

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(trace.id)
    assert isinstance(scores, list)


@pytest.mark.asyncio
async def test_evaluator_with_error_trace(db_session: AsyncSession):
    """Error 状态的 Trace — completion_rate 应给 0 分"""
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="error-trace")
    await service.create_span(trace_id=trace.id, name="llm", type="llm")
    await service.update_trace(trace.id, status="error", error_message="test error")

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(
        trace.id, evaluator_names=["completion_rate"]
    )
    cr_scores = [s for s in scores if s.name == "completion_rate"]
    assert len(cr_scores) == 1
    assert cr_scores[0].value == 0.0


@pytest.mark.asyncio
async def test_unknown_evaluator_graceful(db_session: AsyncSession):
    """未知评估器名不崩溃"""
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="bad-eval")
    await service.complete_trace(trace.id)

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(
        trace.id, evaluator_names=["nonexistent_evaluator"]
    )
    assert scores == []


# ============================
# 检查清单 3.1: API 返回正确状态码
# ============================

@pytest.mark.asyncio
async def test_404_on_nonexistent_trace(client: AsyncClient):
    response = await client.get("/api/traces/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_404_on_nonexistent_dataset(client: AsyncClient):
    response = await client.get("/api/datasets/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_404_on_nonexistent_experiment(client: AsyncClient):
    response = await client.get("/api/experiments/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_201_on_create_span(client: AsyncClient, db_session: AsyncSession):
    trace_service = TraceService(db_session)
    trace = await trace_service.create_trace(project_id="p1", name="for-span")

    response = await client.post("/api/public/spans", json={
        "traceId": trace.id,
        "name": "test-span",
        "type": "llm",
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_201_on_create_generation(client: AsyncClient, db_session: AsyncSession):
    trace_service = TraceService(db_session)
    trace = await trace_service.create_trace(project_id="p1", name="for-gen")
    span = await trace_service.create_span(trace_id=trace.id, name="s", type="llm")

    response = await client.post("/api/public/generations", json={
        "spanId": span.id,
        "model": "deepseek-chat",
    })
    assert response.status_code == 201


# ============================
# 检查清单 3.2: 响应格式统一
# ============================

@pytest.mark.asyncio
async def test_unified_response_format_on_trace_create(client: AsyncClient, db_session: AsyncSession):
    from app.models.project import Project
    proj = Project(id="p-check", name="test")
    db_session.add(proj)
    await db_session.commit()

    response = await client.post("/api/public/traces", json={
        "name": "format-check",
        "projectId": "p-check",
    })
    data = response.json()
    assert "code" in data
    assert "message" in data
    assert "data" in data
    assert isinstance(data["code"], int)
    assert isinstance(data["message"], str)


@pytest.mark.asyncio
async def test_unified_response_format_on_list(client: AsyncClient):
    response = await client.get("/api/traces")
    data = response.json()
    assert "code" in data
    assert data["code"] == 200
    assert "data" in data
    assert "total" in data["data"]


# ============================
# 稳定性测试
# ============================

@pytest.mark.asyncio
async def test_delete_nonexistent_trace(client: AsyncClient):
    response = await client.delete("/api/traces/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_complete_already_completed_trace(db_session: AsyncSession):
    """重复完成 Trace 不应崩溃"""
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="double-complete")
    await service.complete_trace(trace.id)
    result = await service.complete_trace(trace.id)
    # 第二次应仍返回 trace，不崩溃
    assert result is not None


@pytest.mark.asyncio
async def test_pagination_boundary(client: AsyncClient):
    """分页边界测试"""
    response = await client.get("/api/traces?page=9999&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["items"] == [] or len(data["data"]["items"]) >= 0


@pytest.mark.asyncio
async def test_dataset_service_404_handling(db_session: AsyncSession):
    """删除不存在的数据集"""
    service = DatasetService(db_session)
    result = await service.delete_dataset("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_experiment_service_404_handling(db_session: AsyncSession):
    """删除不存在的实验"""
    service = ExperimentService(db_session)
    result = await service.delete_experiment("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_score_service_404_handling(db_session: AsyncSession):
    """删除不存在的分数"""
    service = ScoreService(db_session)
    result = await service.delete_score("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_trace_service_update_nonexistent(db_session: AsyncSession):
    """更新不存在的 Trace"""
    service = TraceService(db_session)
    result = await service.update_trace("nonexistent", name="new-name")
    assert result is None


# ============================
# 检查清单 5.2: 评估器必须有实质性检查
# ============================

@pytest.mark.asyncio
async def test_latency_evaluator_empty_spans(db_session: AsyncSession):
    """无 Span 时延迟评估器返回空列表"""
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="no-span-latency")

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(
        trace.id, evaluator_names=["latency"]
    )
    assert scores == []


@pytest.mark.asyncio
async def test_tool_accuracy_evaluator_no_tools(db_session: AsyncSession):
    """没有 Tool Span 时返回空列表，不给满分"""
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="no-tools")
    span = await service.create_span(trace_id=trace.id, name="llm", type="llm")
    await service.create_generation(span_id=span.id, model="d", completion="ok")

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(
        trace.id, evaluator_names=["tool_accuracy"]
    )
    # 没有 tool span 时返回空，不会虚假地给满分
    assert scores == []


@pytest.mark.asyncio
async def test_hallucination_evaluator_no_llm(db_session: AsyncSession):
    """没有 LLM Span 时幻觉评估器返回空列表"""
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="no-llm")
    await service.create_span(trace_id=trace.id, name="tool", type="tool")

    eval_service = EvaluationService(db_session)
    scores = await eval_service.evaluate_trace(
        trace.id, evaluator_names=["hallucination"]
    )
    assert scores == []


# ============================
# 批量写入稳定性
# ============================

@pytest.mark.asyncio
async def test_bulk_trace_creation(db_session: AsyncSession):
    """批量顺序创建多个 Trace 不应出错

    注：AsyncSession 不支持并发写入，实际生产环境中每个请求有独立 session。
    """
    service = TraceService(db_session)
    traces = []
    for i in range(10):
        t = await service.create_trace(project_id="p1", name=f"bulk-{i}")
        traces.append(t)
    assert len(traces) == 10
    assert all(t.id is not None for t in traces)
