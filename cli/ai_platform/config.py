"""Configuration management for AI Platform CLI."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Config(BaseModel):
    """CLI configuration model."""

    api_url: str = Field(default="http://localhost:8000")
    api_key: Optional[str] = None
    default_model: str = Field(default="gpt-4")
    output_format: str = Field(default="table")  # table, json, yaml


class Settings(BaseSettings):
    """Environment-based settings."""

    AI_PLATFORM_API_URL: str = "http://localhost:8000"
    AI_PLATFORM_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_config_path() -> Path:
    """Get the configuration file path."""
    config_dir = Path.home() / ".ai-platform"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.yaml"


def load_config() -> Config:
    """Load configuration from file and environment."""
    config_path = get_config_path()
    settings = Settings()

    # Start with defaults
    config_data = {}

    # Load from file if exists
    if config_path.exists():
        with open(config_path, "r") as f:
            file_config = yaml.safe_load(f) or {}
            config_data.update(file_config)

    # Override with environment variables
    if settings.AI_PLATFORM_API_URL:
        config_data["api_url"] = settings.AI_PLATFORM_API_URL
    if settings.AI_PLATFORM_API_KEY:
        config_data["api_key"] = settings.AI_PLATFORM_API_KEY

    return Config(**config_data)


def save_config(config: Config) -> None:
    """Save configuration to file."""
    config_path = get_config_path()

    with open(config_path, "w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)


def get_api_key() -> Optional[str]:
    """Get API key from config or environment."""
    config = load_config()
    return config.api_key or os.getenv("AI_PLATFORM_API_KEY")
