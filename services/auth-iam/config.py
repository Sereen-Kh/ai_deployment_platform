"""Configuration for Auth/IAM service."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Auth/IAM service settings."""

    # Service
    SERVICE_NAME: str = "auth-iam"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auth_iam"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", "http://localhost:5173"]

    # OAuth (Future)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
