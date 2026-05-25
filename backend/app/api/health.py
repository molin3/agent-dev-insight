"""健康检查 API"""

from fastapi import APIRouter

from sqlalchemy import text

from app.core.database import engine
from app.core.redis import redis

router = APIRouter()


@router.get("/health")
async def health_check():
    db_healthy = True
    redis_healthy = True

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False

    try:
        await redis.ping()
    except Exception:
        redis_healthy = False

    overall = "healthy" if db_healthy and redis_healthy else "degraded"

    return {
        "code": 200,
        "message": "success",
        "data": {
            "status": overall,
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
        },
    }
