"""RAG (Retrieval-Augmented Generation) routes."""

import asyncio
from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.dependencies import get_current_active_user
from api.models.user import User
from api.models.rag import (
    CollectionCreate,
    CollectionList,
    CollectionResponse,
    Document,
    DocumentCreate,
    DocumentList,
    DocumentResponse,
    RAGQuery,
    RAGResponse,
    RAGStreamChunk,
)
from services.rag_service import RAGService
from services.document_service import DocumentService

router = APIRouter()


# ============= Collection Endpoints =============

@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> CollectionResponse:
    """Create a new vector collection."""
    service = RAGService()
    return await service.create_collection(
        name=collection_data.name,
        description=collection_data.description,
        embedding_model=collection_data.embedding_model,
    )


@router.get("/collections", response_model=CollectionList)
async def list_collections(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> CollectionList:
    """List all collections."""
    service = RAGService()
    collections = await service.list_collections()
    return CollectionList(items=collections, total=len(collections))


@router.delete("/collections/{collection_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_name: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Delete a collection and all its documents."""
    service = RAGService()
    await service.delete_collection(collection_name)


# ============= Document Endpoints =============

@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload and process a document for RAG."""
    # Validate file type
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/plain": "txt",
        "text/markdown": "md",
        "text/csv": "csv",
        "application/json": "json",
    }

    content_type = file.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}",
        )

    service = DocumentService(db)
    document = await service.process_document(
        file=file,
        collection_name=collection_name,
        user_id=current_user.id,
    )

    return DocumentResponse.model_validate(document)


@router.get("/documents", response_model=DocumentList)
async def list_documents(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    collection_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> DocumentList:
    """List documents, optionally filtered by collection."""
    query = select(Document).where(Document.user_id == current_user.id)

    if collection_name:
        query = query.where(Document.collection_name == collection_name)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentList(
        items=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentResponse:
    """Get document details."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentResponse.model_validate(document)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a document and its vectors."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete from vector store
    service = RAGService()
    await service.delete_document_vectors(document.collection_name, str(document_id))

    # Delete from database
    await db.delete(document)
    await db.commit()


# ============= Query Endpoints =============

@router.post("/query", response_model=RAGResponse)
async def query_rag(
    query_data: RAGQuery,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RAGResponse:
    """Query the RAG system."""
    service = RAGService()
    return await service.query(query_data)


@router.post("/query/stream")
async def query_rag_stream(
    query_data: RAGQuery,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StreamingResponse:
    """Query the RAG system with streaming response."""
    service = RAGService()

    async def generate() -> AsyncGenerator[str, None]:
        async for chunk in service.query_stream(query_data):
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============= Search Endpoints =============

@router.post("/search")
async def semantic_search(
    query: str,
    collection_name: str,
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Perform semantic search without LLM generation."""
    service = RAGService()
    chunks = await service.search(
        query=query,
        collection_name=collection_name,
        top_k=top_k,
    )
    return {"chunks": chunks, "count": len(chunks)}
