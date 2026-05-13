"""
配置管理模块
支持多环境配置和环境变量覆盖
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "i3d-agent-system"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", regex="^(development|staging|production)$")

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://app_user:app_pass@localhost:15433/i3d_multitenant"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    REDIS_SESSION_TTL: int = 86400

    # RabbitMQ配置
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_QUEUE: str = "i3d.agent.tasks"

    # MinIO配置
    MINIO_ENDPOINT: str = "172.16.45.33:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_SECURE: bool = False

    # LLM配置
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None

    # 模型配置
    LLM_MODEL_PRIMARY: str = "claude-sonnet-4-20250514"
    LLM_MODEL_FAST: str = "claude-haiku-4-20250123"
    LLM_MODEL_COMPLEX: str = "claude-opus-4-20250514"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # LangSmith配置
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "i3d-agent-system"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # RAG配置
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 10
    RAG_RERANK_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    RAG_BM25_WEIGHT: float = 0.3
    RAG_VECTOR_WEIGHT: float = 0.7

    # Agent配置
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 120
    AGENT_STREAM_RESPONSE: bool = True

    # 租户配置
    SUPPORTED_TENANTS: List[str] = ["shenfa", "meidi", "dongjiang", "huabei"]
    DEFAULT_TENANT: str = "shenfa"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_DIR: str = "./logs"

    # 安全配置
    SECRET_KEY: str = ""
    ALLOWED_ORIGINS: List[str] = ["*"]
    API_KEY_HEADER: str = "X-API-Key"

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def database_url_sync(self) -> str:
        """同步数据库连接URL"""
        return self.DATABASE_URL.replace("+asyncpg", "").replace("+psycopg", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class TenantConfig:
    """租户特定配置"""

    @staticmethod
    def get_bucket_name(tenant_id: str) -> str:
        """获取租户MinIO桶名"""
        return f"{tenant_id}-files"

    @staticmethod
    def get_vector_table(tenant_id: str) -> str:
        """获取租户向量表名"""
        return f"tenant_{tenant_id}_vectors"

    @staticmethod
    def is_valid_tenant(tenant_id: str) -> bool:
        """验证租户ID"""
        settings = Settings()
        return tenant_id in settings.SUPPORTED_TENANTS


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
