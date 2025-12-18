"""RAG (Retrieval-Augmented Generation) models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


# SQLAlchemy Model
class Document(Base):
    """Document database model for RAG."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(500), index=True)
    file_path: Mapped[str] = mapped_column(String(1000))
    file_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(Integer)  # bytes

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )
    collection_name: Mapped[str] = mapped_column(String(255), index=True)

    status: Mapped[str] = mapped_column(
        String(50), default=DocumentStatus.PENDING.value
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing metadata
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    doc_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# Pydantic Schemas
class DocumentBase(BaseModel):
    """Base document schema."""

    name: str = Field(..., max_length=500)
    collection_name: str = Field(..., max_length=255)


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""

    metadata: dict[str, Any] = {}


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    id: UUID
    file_type: str
    file_size: int
    status: DocumentStatus
    chunk_count: int
    token_count: int
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """Schema for document list response."""

    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


# RAG Query/Response Schemas
class RAGQuery(BaseModel):
    """Schema for RAG query request."""

    query: str = Field(..., min_length=1, max_length=10000)
    collection_name: str
    top_k: int = Field(5, ge=1, le=20)
    score_threshold: float = Field(0.7, ge=0, le=1)
    include_metadata: bool = True
    filters: dict[str, Any] = {}

    # LLM settings
    model: Optional[str] = None
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2048, ge=1, le=128000)
    system_prompt: Optional[str] = None


class RetrievedChunk(BaseModel):
    """Schema for a retrieved document chunk."""

    document_id: UUID
    document_name: str
    content: str
    score: float
    metadata: dict[str, Any] = {}
    chunk_index: int


class RAGResponse(BaseModel):
    """Schema for RAG response."""

    answer: str
    query: str
    chunks: list[RetrievedChunk]

    # Metadata
    model_used: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    cached: bool = False


class RAGStreamChunk(BaseModel):
    """Schema for streaming RAG response chunk."""

    type: str  # "chunk", "sources", "done", "error"
    content: Optional[str] = None
    chunks: Optional[list[RetrievedChunk]] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = {}


# Collection Schemas
class CollectionCreate(BaseModel):
    """Schema for creating a vector collection."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    distance_metric: str = "cosine"


class CollectionResponse(BaseModel):
    """Schema for collection response."""

    name: str
    description: Optional[str] = None
    document_count: int
    chunk_count: int
    embedding_model: str
    created_at: datetime


class CollectionList(BaseModel):
    """Schema for collection list response."""

    items: list[CollectionResponse]
    total: int
