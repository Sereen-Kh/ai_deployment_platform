"""Deployment models for database and API."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class DeploymentStatus(str, Enum):
    """Deployment status enum."""

    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETED = "deleted"


class DeploymentType(str, Enum):
    """Deployment type enum."""

    RAG = "rag"
    AGENT = "agent"
    CHAT = "chat"
    COMPLETION = "completion"
    CUSTOM = "custom"


# SQLAlchemy Model
class Deployment(Base):
    """Deployment database model."""

    __tablename__ = "deployments"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    deployment_type: Mapped[str] = mapped_column(
        String(50), default=DeploymentType.RAG.value
    )
    status: Mapped[str] = mapped_column(
        String(50), default=DeploymentStatus.PENDING.value
    )

    # Configuration
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    model_config_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Resources
    replicas: Mapped[int] = mapped_column(Integer, default=1)
    cpu_limit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    memory_limit: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True)

    # Endpoint
    endpoint_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Metadata
    version: Mapped[int] = mapped_column(Integer, default=1)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deployed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="deployments")


# Pydantic Schemas
class ModelConfig(BaseModel):
    """Model configuration schema."""

    provider: str = "openai"
    model: str = "gpt-4-turbo-preview"
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(4096, ge=1, le=128000)
    top_p: float = Field(1.0, ge=0, le=1)
    system_prompt: Optional[str] = None


class RAGConfig(BaseModel):
    """RAG-specific configuration."""

    collection_name: str
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    score_threshold: float = 0.7
    embedding_model: str = "text-embedding-3-small"


class DeploymentConfig(BaseModel):
    """Deployment configuration schema."""

    model: ModelConfig = ModelConfig()
    rag: Optional[RAGConfig] = None
    environment_variables: dict[str, str] = {}
    enable_streaming: bool = True
    enable_caching: bool = True
    cache_ttl: int = 3600


class DeploymentBase(BaseModel):
    """Base deployment schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    deployment_type: DeploymentType = DeploymentType.RAG


class DeploymentCreate(DeploymentBase):
    """Schema for creating a deployment."""

    config: DeploymentConfig = DeploymentConfig()
    replicas: int = Field(1, ge=1, le=10)
    cpu_limit: Optional[str] = "1000m"
    memory_limit: Optional[str] = "2Gi"


class DeploymentUpdate(BaseModel):
    """Schema for updating a deployment."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[DeploymentConfig] = None
    replicas: Optional[int] = Field(None, ge=1, le=10)
    cpu_limit: Optional[str] = None
    memory_limit: Optional[str] = None


class DeploymentResponse(DeploymentBase):
    """Schema for deployment response."""

    id: UUID
    user_id: UUID
    status: DeploymentStatus
    config: dict[str, Any]
    replicas: int
    endpoint_url: Optional[str] = None
    version: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deployed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeploymentList(BaseModel):
    """Schema for deployment list response."""

    items: list[DeploymentResponse]
    total: int
    page: int
    page_size: int


class DeploymentStats(BaseModel):
    """Schema for deployment statistics."""

    deployment_id: UUID
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    total_tokens: int
    estimated_cost: float
    period: str  # e.g., "24h", "7d", "30d"
