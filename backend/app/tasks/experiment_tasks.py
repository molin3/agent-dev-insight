"""Celery Experiment 异步任务"""

import asyncio
import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def run_experiment_task(self, experiment_id: str, model_names: list[str] | None = None) -> dict:
    """异步执行实验：对多个模型运行测试用例并对比"""
    logger.info("Running experiment: %s", experiment_id)

    async def _run():
        from app.core.database import async_session_factory
        from app.services.experiment_service import ExperimentService

        async with async_session_factory() as db:
            service = ExperimentService(db)
            exp = await service.run_experiment(experiment_id, model_names=model_names)
            if exp is None:
                return {"experiment_id": experiment_id, "status": "not_found"}
            logger.info("Experiment completed: %s (status=%s)", experiment_id, exp.status)
            return {"experiment_id": experiment_id, "status": exp.status}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("run_experiment failed for %s: %s", experiment_id, exc)
        raise self.retry(exc=exc)
