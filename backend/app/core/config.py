"""AgentDevInsight 配置管理"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 应用
    app_name: str = "AgentDevInsight"
    app_version: str = "0.1.0"
    debug: bool = False

    # 数据库
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentdev"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/agentdev"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # LLM（用于 LLM-as-Judge 评估）
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: Optional[str] = None
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # SDK 数据采集
    sdk_ingestion_mode: str = "sync"  # "celery" or "sync"
    sdk_ingestion_timeout: int = 5

    # 评估
    eval_max_concurrency: int = 5
    eval_default_model: str = "gpt-4o"

    # 实验/回归
    experiment_max_concurrency: int = 10


settings = Settings()


def get_settings() -> Settings:
    return settings
