"""Redis 连接管理"""

import redis.asyncio as aioredis

from app.core.config import settings

redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def init_redis() -> None:
    try:
        await redis.ping()
    except Exception:
        pass  # Redis 不可用时不影响启动


async def close_redis() -> None:
    try:
        await redis.close()
    except Exception:
        pass
