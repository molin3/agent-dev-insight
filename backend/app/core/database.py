"""数据库连接管理"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_size=20,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    async with engine.begin() as conn:
        from app.models.api_key import APIKey  # noqa: F401
        from app.models.project import Project  # noqa: F401
        from app.models.trace import Generation, Span, Trace  # noqa: F401
        from app.models.score import Score  # noqa: F401
        from app.models.dataset import Dataset, DatasetItem, DatasetRun  # noqa: F401
        from app.models.experiment import (  # noqa: F401
            ComparisonResult,
            Experiment,
            ExperimentRun,
        )

        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await engine.dispose()
