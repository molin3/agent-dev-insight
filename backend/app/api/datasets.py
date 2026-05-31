"""Dataset 管理 API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.dataset_service import DatasetService

router = APIRouter()


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class DatasetUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None


class DatasetItemCreate(BaseModel):
    input: dict
    expected_output: str | None = None
    eval_criteria: str | None = None


class DatasetItemBulkImport(BaseModel):
    items: list[dict] = Field(..., min_length=1, max_length=500)


@router.post("/datasets", status_code=201)
async def create_dataset(
    request: DatasetCreate,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    ds = await service.create_dataset(request.name, request.description)
    return {"code": 201, "message": "Dataset created", "data": ds.to_dict()}


@router.get("/datasets")
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    result = await service.get_datasets(page=page, page_size=page_size)
    return {"code": 200, "message": "success", "data": result}


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    service = DatasetService(db)
    ds = await service.get_dataset(dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    items_result = await service.get_items(dataset_id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "dataset": ds.to_dict(),
            "items": [i.to_dict() for i in items_result["items"]],
        },
    }


@router.patch("/datasets/{dataset_id}")
async def update_dataset(
    dataset_id: str,
    request: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    ds = await service.update_dataset(
        dataset_id, name=request.name, description=request.description
    )
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"code": 200, "message": "Dataset updated", "data": ds.to_dict()}


@router.get("/datasets/{dataset_id}/items")
async def list_items(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    ds = await service.get_dataset(dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    result = await service.get_items(dataset_id, page=page, page_size=page_size)
    result["items"] = [i.to_dict() for i in result["items"]]
    return {"code": 200, "message": "success", "data": result}


@router.post("/datasets/{dataset_id}/items", status_code=201)
async def add_item(
    dataset_id: str,
    request: DatasetItemCreate,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    item = await service.add_item(
        dataset_id=dataset_id,
        input=request.input,
        expected_output=request.expected_output,
        eval_criteria=request.eval_criteria,
    )
    return {"code": 201, "message": "Item added", "data": item.to_dict()}


@router.post("/datasets/{dataset_id}/items/bulk", status_code=201)
async def bulk_import_items(
    dataset_id: str,
    request: DatasetItemBulkImport,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    ds = await service.get_dataset(dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    count = await service.add_items_bulk(dataset_id, request.items)
    return {"code": 201, "message": f"Imported {count} items", "data": {"count": count}}


@router.post("/datasets/{dataset_id}/items/from-trace", status_code=201)
async def add_item_from_trace(
    dataset_id: str,
    trace_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    item = await service.create_item_from_trace(dataset_id, trace_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {"code": 201, "message": "Item created from trace", "data": item.to_dict()}


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    service = DatasetService(db)
    deleted = await service.delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"code": 200, "message": "Dataset deleted", "data": None}


@router.delete("/datasets/{dataset_id}/items/{item_id}")
async def delete_item(
    dataset_id: str, item_id: str, db: AsyncSession = Depends(get_db)
):
    service = DatasetService(db)
    deleted = await service.delete_item(dataset_id, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"code": 200, "message": "Item deleted", "data": None}
