"""Experiment 管理 API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.experiment_service import ExperimentService

router = APIRouter()


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    task_description: str = Field(..., min_length=1)
    dataset_id: str | None = None


@router.post("/experiments", status_code=201)
async def create_experiment(
    request: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)
    exp = await service.create_experiment(
        name=request.name,
        task_description=request.task_description,
        description=request.description,
        dataset_id=request.dataset_id,
    )
    # 自动执行实验
    exp = await service.run_experiment(exp.id)
    return {"code": 201, "message": "Experiment created and running", "data": exp.to_dict() if exp else {}}


@router.get("/experiments")
async def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)
    result = await service.get_experiments(page=page, page_size=page_size)
    return {"code": 200, "message": "success", "data": result}


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    service = ExperimentService(db)
    exp = await service.get_experiment(experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    comparison = await service.get_comparison_data(experiment_id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "experiment": exp.to_dict(),
            "comparison": comparison,
            "runs": [r.to_dict() for r in exp.runs],
        },
    }


@router.post("/experiments/{experiment_id}/run")
async def run_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    service = ExperimentService(db)
    exp = await service.run_experiment(experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "code": 200,
        "message": f"Experiment {exp.status}",
        "data": exp.to_dict(),
    }


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    service = ExperimentService(db)
    deleted = await service.delete_experiment(experiment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"code": 200, "message": "Experiment deleted", "data": None}
