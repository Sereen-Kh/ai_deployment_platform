"""API Key models for database and API."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


# SQLAlchemy Model
class APIKey(Base):
    """API Key database model."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    key_prefix: Mapped[str] = mapped_column(
        String(10))  # First 8 chars for display
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )

    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="api_keys")


# Pydantic Schemas
class APIKeyBase(BaseModel):
    """Base API key schema."""

    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=lambda: ["read", "write"])


class APIKeyCreate(APIKeyBase):
    """Schema for creating an API key."""

    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(APIKeyBase):
    """Schema for API key response (without the actual key)."""

    id: UUID
    key_prefix: str
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreated(APIKeyResponse):
    """Response when API key is first created (includes full key)."""

    key: str  # Only returned once on creation


class APIKeyList(BaseModel):
    """Schema for API key list response."""

    items: list[APIKeyResponse]
    total: int
