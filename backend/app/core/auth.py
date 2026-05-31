"""API Key 认证中间件"""

import secrets
import logging

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """生成安全的 API Key"""
    return f"adi-{secrets.token_hex(24)}"


async def get_api_key_from_request(request: Request) -> str | None:
    """从请求中提取 API Key（支持 header 和 query param）"""
    # 优先从 header 获取
    key = request.headers.get("X-API-Key")
    if key:
        return key

    # 支持 Authorization: Bearer <key>
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]

    # 开发模式支持 query param
    return request.query_params.get("api_key")


async def verify_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> str:
    """验证 API Key，返回 project_id"""
    from app.models.api_key import APIKey

    key = await get_api_key_from_request(request)
    if not key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    result = await db.execute(
        select(APIKey).where(APIKey.key == key, APIKey.is_active == True)  # noqa: E712
    )
    api_key_obj = result.scalar_one_or_none()
    if api_key_obj is None:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    return api_key_obj.project_id


async def verify_api_key_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> str | None:
    """可选认证：有 Key 则验证，无 Key 则返回 None（开发模式）"""
    from app.core.config import settings

    key = await get_api_key_from_request(request)
    if not key:
        return None

    return await verify_api_key(request, db)
