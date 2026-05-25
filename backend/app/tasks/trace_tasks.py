"""Celery Trace 异步任务"""

import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def enrich_trace(self, trace_id: str) -> dict:
    """后处理 Trace：计算成本、运行评估器"""
    # 同步模式下不需要异步处理
    # Celery worker 运行时执行成本计算和评估触发
    logger.info("Enriching trace: %s (attempt %d)", trace_id, self.request.retries)
    return {"trace_id": trace_id, "status": "enriched"}


@celery_app.task(bind=True, max_retries=3)
def finalize_trace(self, trace_id: str) -> dict:
    """完成 Trace：汇总数据、触发评估"""
    logger.info("Finalizing trace: %s", trace_id)
    return {"trace_id": trace_id, "status": "finalized"}
