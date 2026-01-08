"""Application configuration settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Development Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development",
                             pattern="^(development|staging|production)$")

    # API
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = [
        "http://localhost:3000", "http://localhost:5173"]

    # Security
    secret_key: str = Field(
        default="your-super-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_platform"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_ttl: int = 3600  # 1 hour

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"

    # Google Gemini (Primary - Free tier available)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "models/text-embedding-004"

    # OpenAI (Optional)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"

    # Anthropic (Optional)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"

    # LLM Settings
    # Use "mock" for testing without API keys, or "gemini", "openai", "anthropic"
    default_llm_provider: str = "mock"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # Storage
    storage_type: str = "local"  # local, s3, gcs
    storage_bucket: Optional[str] = None
    upload_max_size_mb: int = 50

    # Monitoring
    sentry_dsn: Optional[str] = None
    prometheus_enabled: bool = True

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def async_database_url(self) -> str:
        """Get async database URL."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
