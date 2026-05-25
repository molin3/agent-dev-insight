"""AgentDevInsight API 依赖"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
    db: AsyncSession,
    query,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """通用分页辅助函数"""
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    items_query = query.offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(items_query)).scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }
