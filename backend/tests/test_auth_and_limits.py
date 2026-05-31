"""认证、限流和 Dashboard 聚合测试"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import generate_api_key
from app.core.rate_limit import RateLimiter
from app.models.api_key import APIKey


# ===== API Key 认证测试 =====

@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, db_session: AsyncSession):
    """创建 API Key"""
    resp = await client.post("/api/auth/keys", json={"name": "test-key", "project_id": "p1"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 201
    assert data["data"]["key"].startswith("adi-")
    assert data["data"]["project_id"] == "p1"


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient, db_session: AsyncSession):
    """列出 API Keys（脱敏）"""
    # 先创建一个
    await client.post("/api/auth/keys", json={"name": "key-1"})
    resp = await client.get("/api/auth/keys")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert "key_prefix" in data[0]
    assert "..." in data[0]["key_prefix"]


@pytest.mark.asyncio
async def test_delete_api_key(client: AsyncClient, db_session: AsyncSession):
    """禁用 API Key"""
    resp = await client.post("/api/auth/keys", json={"name": "to-delete"})
    key_id = resp.json()["data"]["id"]

    resp = await client.delete(f"/api/auth/keys/{key_id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_nonexistent_api_key(client: AsyncClient):
    """删除不存在的 Key"""
    resp = await client.delete("/api/auth/keys/nonexistent")
    assert resp.status_code == 404


def test_generate_api_key_format():
    """API Key 格式验证"""
    key = generate_api_key()
    assert key.startswith("adi-")
    assert len(key) == 4 + 48  # prefix + hex


# ===== 限流测试 =====

def test_rate_limiter_allows_within_limit():
    """限流器：限额内允许"""
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.check("test-key") is True
    assert limiter.check("test-key") is True
    assert limiter.check("test-key") is True
    assert limiter.remaining("test-key") == 0


def test_rate_limiter_blocks_over_limit():
    """限流器：超限后拒绝"""
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    assert limiter.check("key-1") is True
    assert limiter.check("key-1") is True
    assert limiter.check("key-1") is False


def test_rate_limiter_per_key_isolation():
    """限流器：不同 Key 相互隔离"""
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.check("key-a") is True
    assert limiter.check("key-a") is False
    assert limiter.check("key-b") is True  # 不受影响


# ===== Dashboard 聚合测试 =====

@pytest.mark.asyncio
async def test_dashboard_overview_empty(client: AsyncClient):
    """Dashboard：无数据时返回零值"""
    resp = await client.get("/api/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_traces"] == 0
    assert data["completed"] == 0
    assert data["total_tokens"] == 0


@pytest.mark.asyncio
async def test_dashboard_overview_with_data(client: AsyncClient, db_session: AsyncSession):
    """Dashboard：有数据时正确聚合"""
    from app.services.trace_service import TraceService

    service = TraceService(db_session)
    # 创建 2 个 completed trace
    t1 = await service.create_trace(project_id="p1", name="t1")
    await service.complete_trace(t1.id)
    t2 = await service.create_trace(project_id="p1", name="t2")
    await service.complete_trace(t2.id)
    # 创建 1 个 in_progress trace
    await service.create_trace(project_id="p1", name="t3")

    resp = await client.get("/api/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_traces"] >= 3
    assert data["completed"] >= 2


# ===== 输入校验测试 =====

@pytest.mark.asyncio
async def test_validation_error_format(client: AsyncClient):
    """验证错误返回统一格式"""
    # 发送空 body 创建 dataset
    resp = await client.post("/api/datasets", json={})
    assert resp.status_code == 422
    data = resp.json()
    assert data["code"] == 422
    assert "message" in data
    assert data["data"] is None
