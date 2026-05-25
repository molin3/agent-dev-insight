"""Trace 服务和 API 集成测试"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trace_service import TraceService
from app.services.score_service import ScoreService


@pytest.mark.asyncio
async def test_create_trace(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(
        project_id="test-project",
        name="test-trace",
        user_id="user-1",
        tags=["test", "v1"],
    )
    assert trace.id is not None
    assert trace.name == "test-trace"
    assert trace.status == "in_progress"
    assert trace.project_id == "test-project"


@pytest.mark.asyncio
async def test_create_and_get_trace(db_session: AsyncSession):
    service = TraceService(db_session)
    created = await service.create_trace(project_id="p1", name="trace-1")
    fetched = await service.get_trace(created.id)
    assert fetched is not None
    assert fetched.name == "trace-1"


@pytest.mark.asyncio
async def test_get_traces_pagination(db_session: AsyncSession):
    service = TraceService(db_session)
    for i in range(5):
        await service.create_trace(project_id="p1", name=f"trace-{i}")

    result = await service.get_traces(project_id="p1", page=1, page_size=3)
    assert result["total"] == 5
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_create_span(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(
        trace_id=trace.id,
        name="llm-call",
        type="llm",
        model="deepseek-chat",
        input={"prompt": "hello"},
    )
    assert span.trace_id == trace.id
    assert span.type == "llm"
    assert span.status == "in_progress"


@pytest.mark.asyncio
async def test_complete_span(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(trace_id=trace.id, name="tool-call", type="tool")
    updated = await service.complete_span(
        span.id, output={"result": "ok"}, usage={"total_tokens": 100}
    )
    assert updated.status == "completed"
    assert updated.output == {"result": "ok"}


@pytest.mark.asyncio
async def test_create_generation(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(trace_id=trace.id, name="llm", type="llm")
    gen = await service.create_generation(
        span_id=span.id,
        model="deepseek-chat",
        prompt=[{"role": "user", "content": "hi"}],
        completion="Hello!",
        usage={"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        cost=0.001,
    )
    assert gen.model == "deepseek-chat"
    assert gen.completion == "Hello!"


@pytest.mark.asyncio
async def test_complete_trace(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(trace_id=trace.id, name="llm", type="llm")
    await service.create_generation(
        span_id=span.id,
        model="deepseek-chat",
        usage={"total_tokens": 50},
        cost=0.002,
    )
    completed = await service.complete_trace(trace.id)
    assert completed.status == "completed"
    assert completed.total_tokens == 50
    assert completed.total_cost == 0.002
    assert completed.total_latency_ms is not None


@pytest.mark.asyncio
async def test_delete_trace(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    assert await service.delete_trace(trace.id) is True
    assert await service.get_trace(trace.id) is None


@pytest.mark.asyncio
async def test_get_trace_replay(db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    span = await service.create_span(trace_id=trace.id, name="llm", type="llm")
    await service.create_generation(span_id=span.id, model="d", completion="ok")
    events = await service.get_trace_replay(trace.id)
    assert len(events) == 2  # span event + generation event


@pytest.mark.asyncio
async def test_create_score(db_session: AsyncSession):
    service = TraceService(db_session)
    score_service = ScoreService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    score = await score_service.create_score(
        trace_id=trace.id,
        name="completeness",
        value=0.95,
        comment="good",
    )
    assert score.name == "completeness"
    assert score.value == 0.95


@pytest.mark.asyncio
async def test_scores_for_trace(db_session: AsyncSession):
    service = TraceService(db_session)
    score_service = ScoreService(db_session)
    trace = await service.create_trace(project_id="p1", name="t1")
    await score_service.create_score(trace_id=trace.id, name="accuracy", value=0.8)
    await score_service.create_score(trace_id=trace.id, name="latency", value=0.9)
    scores = await score_service.get_scores_for_trace(trace.id)
    assert len(scores) == 2


@pytest.mark.asyncio
async def test_create_trace_via_api(client: AsyncClient, db_session: AsyncSession):
    from app.models.project import Project

    proj = Project(id="proj-001", name="default")
    db_session.add(proj)
    await db_session.commit()

    response = await client.post("/api/public/traces", json={
        "name": "api-trace",
        "projectId": "proj-001",
        "tags": ["api-test"],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["id"] is not None


@pytest.mark.asyncio
async def test_get_trace_detail_via_api(client: AsyncClient, db_session: AsyncSession):
    service = TraceService(db_session)
    trace = await service.create_trace(project_id="p1", name="api-detail-test")

    response = await client.get(f"/api/traces/{trace.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "api-detail-test"


@pytest.mark.asyncio
async def test_get_traces_list_via_api(client: AsyncClient, db_session: AsyncSession):
    service = TraceService(db_session)
    for i in range(3):
        await service.create_trace(project_id="p1", name=f"list-{i}")

    response = await client.get("/api/traces?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 3
    assert len(data["data"]["items"]) == 2
