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

    # 数据库（通过 DATABASE_URL 环境变量配置，默认 SQLite）
    database_url: str = "sqlite+aiosqlite:///./agentdev.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # LLM（用于 LLM-as-Judge 评估）
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: Optional[str] = None
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # 数据采集模式：sync（同步）或 celery（异步）
    sdk_ingestion_mode: str = "sync"


settings = Settings()


def get_settings() -> Settings:
    return settings
