"""基础冒烟测试"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "AgentDevInsight"


async def test_settings_load():
    from app.core.config import settings

    assert settings.app_name == "AgentDevInsight"
    assert settings.app_version == "0.1.0"


def test_uuid_generation():
    from app.utils.helpers import gen_uuid

    uid = gen_uuid()
    assert len(uid) == 36
    assert uid.count("-") == 4


def test_safe_truncate():
    from app.utils.helpers import safe_truncate

    assert safe_truncate("hello", max_len=10) == "hello"
    assert safe_truncate("x" * 100, max_len=50) == "x" * 50 + "..."
