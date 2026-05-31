"""API Key 管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import generate_api_key
from app.core.database import get_db
from app.models.api_key import APIKey

router = APIRouter()


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    project_id: str = Field("default", max_length=36)


@router.post("/auth/keys", status_code=201)
async def create_api_key(
    request: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新的 API Key（开发用，生产环境应有更严格的认证）"""
    key_value = generate_api_key()
    api_key = APIKey(
        name=request.name,
        key=key_value,
        project_id=request.project_id,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return {
        "code": 201,
        "message": "API Key created",
        "data": {
            "id": api_key.id,
            "name": api_key.name,
            "key": key_value,
            "project_id": api_key.project_id,
        },
    }


@router.get("/auth/keys")
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    """列出所有 API Key（key 字段脱敏）"""
    result = await db.execute(
        select(APIKey).where(APIKey.is_active == True).order_by(APIKey.created_at.desc())  # noqa: E712
    )
    keys = result.scalars().all()
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": k.id,
                "name": k.name,
                "key_prefix": k.key[:10] + "...",
                "project_id": k.project_id,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat(),
            }
            for k in keys
        ],
    }


@router.delete("/auth/keys/{key_id}")
async def delete_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    """禁用 API Key"""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="API Key not found")
    api_key.is_active = False
    await db.commit()
    return {"code": 200, "message": "API Key disabled", "data": None}
