"""Shared Pydantic models and enums."""

from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


# Common Enums
class DeploymentStatus(str, Enum):
    """Deployment lifecycle states."""
    CREATED = "created"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"
    SCALING = "scaling"
    UPDATING = "updating"


class ModelType(str, Enum):
    """Model types supported."""
    CUSTOM = "custom"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    VLLM = "vllm"


class DeploymentType(str, Enum):
    """Deployment types."""
    REALTIME_API = "realtime_api"
    BATCH = "batch"
    SCHEDULED = "scheduled"
    EDGE = "edge"
    SERVERLESS = "serverless"


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class InferenceFramework(str, Enum):
    """Inference runtime frameworks."""
    FASTAPI = "fastapi"
    VLLM = "vllm"
    TRITON = "triton"
    TGI = "tgi"
    ONNX = "onnx"


# Common Response Models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Success response wrapper."""
    success: bool = True
    message: str
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Service-to-Service Communication Models
class ServiceRequest(BaseModel):
    """Base model for inter-service requests."""
    request_id: str
    source_service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ServiceResponse(BaseModel):
    """Base model for inter-service responses."""
    success: bool
    request_id: str
    data: Optional[Any] = None
    error: Optional[str] = None
