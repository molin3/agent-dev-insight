"""Celery Trace 异步任务"""

import asyncio
import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_async_session():
    """获取异步数据库会话（用于 Celery 同步上下文）"""
    from app.core.database import async_session_factory
    return async_session_factory()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def enrich_trace(self, trace_id: str) -> dict:
    """后处理 Trace：计算聚合指标（Token、成本、延迟）"""
    logger.info("Enriching trace: %s", trace_id)

    async def _enrich():
        from app.core.database import async_session_factory
        from app.services.trace_service import TraceService

        async with async_session_factory() as db:
            service = TraceService(db)
            trace = await service.get_trace(trace_id)
            if trace is None:
                logger.warning("Trace not found: %s", trace_id)
                return {"trace_id": trace_id, "status": "not_found"}

            # complete_trace 会计算延迟、token、成本等聚合指标
            await service.complete_trace(trace_id)
            logger.info("Trace enriched: %s", trace_id)
            return {"trace_id": trace_id, "status": "enriched"}

    try:
        return asyncio.run(_enrich())
    except Exception as exc:
        logger.error("enrich_trace failed for %s: %s", trace_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def finalize_trace(self, trace_id: str) -> dict:
    """完成 Trace：触发评估器运行"""
    logger.info("Finalizing trace: %s", trace_id)

    async def _finalize():
        from app.core.database import async_session_factory
        from app.services.evaluation_service import EvaluationService
        from app.services.trace_service import TraceService

        async with async_session_factory() as db:
            # 确保 trace 已完成
            trace_service = TraceService(db)
            trace = await service.get_trace(trace_id) if (service := trace_service) else None
            if trace is None:
                return {"trace_id": trace_id, "status": "not_found"}

            # 运行评估
            eval_service = EvaluationService(db)
            scores = await eval_service.evaluate_trace(trace_id)
            logger.info("Trace %s evaluated: %d scores", trace_id, len(scores))
            return {"trace_id": trace_id, "status": "finalized", "scores": len(scores)}

    try:
        return asyncio.run(_finalize())
    except Exception as exc:
        logger.error("finalize_trace failed for %s: %s", trace_id, exc)
        raise self.retry(exc=exc)
