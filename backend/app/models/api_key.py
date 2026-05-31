"""API Key 模型"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class APIKey(BaseModel):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, default="default")
    is_active: Mapped[bool] = mapped_column(default=True)
