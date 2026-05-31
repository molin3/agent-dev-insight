"""Dataset 服务测试"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dataset_service import DatasetService


@pytest.mark.asyncio
async def test_create_dataset(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds = await service.create_dataset(name="test-dataset", description="A test dataset")
    assert ds.id is not None
    assert ds.name == "test-dataset"
    assert ds.description == "A test dataset"


@pytest.mark.asyncio
async def test_get_dataset(db_session: AsyncSession):
    service = DatasetService(db_session)
    created = await service.create_dataset(name="ds-1")
    fetched = await service.get_dataset(created.id)
    assert fetched is not None
    assert fetched.name == "ds-1"


@pytest.mark.asyncio
async def test_get_datasets_pagination(db_session: AsyncSession):
    service = DatasetService(db_session)
    for i in range(5):
        await service.create_dataset(name=f"ds-{i}")

    result = await service.get_datasets(page=1, page_size=3)
    assert result["total"] == 5
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_update_dataset(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds = await service.create_dataset(name="old-name")
    updated = await service.update_dataset(ds.id, name="new-name")
    assert updated is not None
    assert updated.name == "new-name"


@pytest.mark.asyncio
async def test_update_dataset_not_found(db_session: AsyncSession):
    service = DatasetService(db_session)
    result = await service.update_dataset("nonexistent", name="x")
    assert result is None


@pytest.mark.asyncio
async def test_delete_dataset(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds = await service.create_dataset(name="to-delete")
    deleted = await service.delete_dataset(ds.id)
    assert deleted is True
    assert await service.get_dataset(ds.id) is None


@pytest.mark.asyncio
async def test_delete_dataset_not_found(db_session: AsyncSession):
    service = DatasetService(db_session)
    deleted = await service.delete_dataset("nonexistent")
    assert deleted is False


@pytest.mark.asyncio
async def test_add_item(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds = await service.create_dataset(name="ds-with-items")
    item = await service.add_item(ds.id, input={"query": "hello"}, expected_output="world")
    assert item.id is not None
    assert item.dataset_id == ds.id
    assert item.input == {"query": "hello"}


@pytest.mark.asyncio
async def test_get_items(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds = await service.create_dataset(name="ds-items")
    for i in range(3):
        await service.add_item(ds.id, input={"idx": i})

    result = await service.get_items(ds.id)
    assert result["total"] == 3
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_delete_item(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds = await service.create_dataset(name="ds-del-item")
    item = await service.add_item(ds.id, input={"key": "val"})

    deleted = await service.delete_item(ds.id, item.id)
    assert deleted is True

    result = await service.get_items(ds.id)
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_delete_item_wrong_dataset(db_session: AsyncSession):
    service = DatasetService(db_session)
    ds1 = await service.create_dataset(name="ds1")
    ds2 = await service.create_dataset(name="ds2")
    item = await service.add_item(ds1.id, input={"key": "val"})

    deleted = await service.delete_item(ds2.id, item.id)
    assert deleted is False
