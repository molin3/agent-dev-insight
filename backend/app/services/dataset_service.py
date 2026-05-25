"""Dataset 服务"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset, DatasetItem, DatasetRun
from app.utils.helpers import gen_uuid


class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dataset(self, name: str, description: str | None = None) -> Dataset:
        dataset = Dataset(id=gen_uuid(), name=name, description=description)
        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)
        return dataset

    async def get_dataset(self, dataset_id: str) -> Dataset | None:
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        return result.scalar_one_or_none()

    async def get_datasets(self, page: int = 1, page_size: int = 20) -> dict:
        query = select(Dataset).order_by(Dataset.created_at.desc())
        count_query = select(func.count()).select_from(Dataset)
        total = (await self.db.execute(count_query)).scalar() or 0
        items = (
            await self.db.execute(query.offset((page - 1) * page_size).limit(page_size))
        ).scalars().all()
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    async def add_item(
        self,
        dataset_id: str,
        input: dict,
        expected_output: str | None = None,
        eval_criteria: str | None = None,
        source_trace_id: str | None = None,
    ) -> DatasetItem:
        item = DatasetItem(
            id=gen_uuid(),
            dataset_id=dataset_id,
            input=input,
            expected_output=expected_output,
            eval_criteria=eval_criteria,
            source_trace_id=source_trace_id,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def create_item_from_trace(self, dataset_id: str, trace_id: str) -> DatasetItem | None:
        from app.services.trace_service import TraceService

        trace_service = TraceService(self.db)
        trace = await trace_service.get_trace(trace_id)
        if trace is None:
            return None

        gen_completions = []
        for span in trace.spans:
            for gen in span.generations:
                if gen.completion:
                    gen_completions.append(gen.completion)

        return await self.add_item(
            dataset_id=dataset_id,
            input={"trace_name": trace.name, "trace_id": trace_id},
            expected_output="\n".join(gen_completions) if gen_completions else None,
            source_trace_id=trace_id,
        )

    async def get_items(self, dataset_id: str) -> list[DatasetItem]:
        result = await self.db.execute(
            select(DatasetItem)
            .where(DatasetItem.dataset_id == dataset_id)
            .order_by(DatasetItem.created_at)
        )
        return list(result.scalars().all())

    async def delete_dataset(self, dataset_id: str) -> bool:
        dataset = await self.get_dataset(dataset_id)
        if dataset is None:
            return False
        await self.db.delete(dataset)
        await self.db.commit()
        return True

    async def create_run(self, dataset_id: str) -> DatasetRun:
        run = DatasetRun(id=gen_uuid(), dataset_id=dataset_id, status="pending")
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def complete_run(self, run_id: str, passed: int, failed: int) -> DatasetRun | None:
        result = await self.db.execute(select(DatasetRun).where(DatasetRun.id == run_id))
        run = result.scalar_one_or_none()
        if run is None:
            return None
        run.passed_items = passed
        run.failed_items = failed
        run.total_items = passed + failed
        run.pass_rate = passed / run.total_items if run.total_items > 0 else 0.0
        run.status = "completed"
        await self.db.commit()
        await self.db.refresh(run)
        return run
