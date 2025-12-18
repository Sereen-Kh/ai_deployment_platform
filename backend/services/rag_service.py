"""RAG Service for retrieval-augmented generation."""

import hashlib
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from core.config import settings
from core.redis import cache
from api.models.rag import (
    CollectionResponse,
    RAGQuery,
    RAGResponse,
    RAGStreamChunk,
    RetrievedChunk,
)
from services.llm_service import llm_service

logger = structlog.get_logger()


class RAGService:
    """Service for RAG operations."""

    def __init__(self):
        self.qdrant = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )

    async def create_collection(
        self,
        name: str,
        description: Optional[str] = None,
        embedding_model: str = "models/text-embedding-004",
        vector_size: int = 768,  # Gemini text-embedding-004 uses 768 dimensions
    ) -> CollectionResponse:
        """Create a new vector collection."""
        try:
            self.qdrant.create_collection(
                collection_name=name,
                vectors_config=qdrant_models.VectorParams(
                    size=vector_size,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )

            logger.info("Created collection", name=name)

            return CollectionResponse(
                name=name,
                description=description,
                document_count=0,
                chunk_count=0,
                embedding_model=embedding_model,
                created_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error("Failed to create collection",
                         name=name, error=str(e))
            raise

    async def list_collections(self) -> list[CollectionResponse]:
        """List all collections."""
        collections = self.qdrant.get_collections()
        result = []

        for collection in collections.collections:
            info = self.qdrant.get_collection(collection.name)
            result.append(
                CollectionResponse(
                    name=collection.name,
                    description=None,
                    document_count=0,  # Would need to track this separately
                    chunk_count=info.points_count or 0,
                    embedding_model="models/text-embedding-004",
                    created_at=datetime.utcnow(),
                )
            )

        return result

    async def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            self.qdrant.delete_collection(collection_name=name)
            logger.info("Deleted collection", name=name)
            return True
        except Exception as e:
            logger.error("Failed to delete collection",
                         name=name, error=str(e))
            raise

    async def add_chunks(
        self,
        collection_name: str,
        chunks: list[dict[str, Any]],
    ) -> int:
        """Add document chunks to collection."""
        if not chunks:
            return 0

        # Get embeddings for all chunks
        texts = [chunk["content"] for chunk in chunks]
        embeddings = await llm_service.create_embeddings_batch(texts)

        # Prepare points
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = chunk.get("id") or hashlib.md5(
                f"{chunk['document_id']}_{chunk['chunk_index']}".encode()
            ).hexdigest()

            points.append(
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "content": chunk["content"],
                        "document_id": str(chunk["document_id"]),
                        "document_name": chunk.get("document_name", ""),
                        "chunk_index": chunk.get("chunk_index", i),
                        "metadata": chunk.get("metadata", {}),
                    },
                )
            )

        # Upsert to Qdrant
        self.qdrant.upsert(
            collection_name=collection_name,
            points=points,
        )

        logger.info(
            "Added chunks to collection",
            collection=collection_name,
            count=len(points),
        )

        return len(points)

    async def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[dict] = None,
    ) -> list[RetrievedChunk]:
        """Perform semantic search."""
        # Get query embedding
        query_embedding = await llm_service.create_embedding(query)

        # Build filter if provided
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=f"metadata.{key}",
                        match=qdrant_models.MatchValue(value=value),
                    )
                )
            qdrant_filter = qdrant_models.Filter(must=conditions)

        # Search
        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
        )

        # Convert to response model
        chunks = []
        for result in results:
            chunks.append(
                RetrievedChunk(
                    document_id=result.payload["document_id"],
                    document_name=result.payload.get("document_name", ""),
                    content=result.payload["content"],
                    score=result.score,
                    metadata=result.payload.get("metadata", {}),
                    chunk_index=result.payload.get("chunk_index", 0),
                )
            )

        return chunks

    async def query(self, query_data: RAGQuery) -> RAGResponse:
        """Perform RAG query with LLM generation."""
        start_time = time.time()

        # Check cache
        cache_key = f"rag:{hashlib.md5(f'{query_data.query}:{query_data.collection_name}'.encode(
        )).hexdigest()}"
        cached = await cache.get(cache_key)
        if cached:
            return RAGResponse(**cached, cached=True)

        # Retrieve relevant chunks
        chunks = await self.search(
            query=query_data.query,
            collection_name=query_data.collection_name,
            top_k=query_data.top_k,
            score_threshold=query_data.score_threshold,
            filters=query_data.filters,
        )

        # Build context from chunks
        context = "\n\n---\n\n".join([
            f"Source: {chunk.document_name}\n{chunk.content}"
            for chunk in chunks
        ])

        # Build prompt
        system_prompt = query_data.system_prompt or """You are a helpful AI assistant. 
Answer the user's question based on the provided context. 
If the context doesn't contain relevant information, say so.
Always cite your sources when possible."""

        prompt = f"""Context:
{context}

Question: {query_data.query}

Answer:"""

        # Generate response
        llm_result = await llm_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=query_data.model,
            temperature=query_data.temperature,
            max_tokens=query_data.max_tokens,
        )

        latency_ms = (time.time() - start_time) * 1000

        response = RAGResponse(
            answer=llm_result["response"],
            query=query_data.query,
            chunks=chunks,
            model_used=llm_result["model"],
            total_tokens=llm_result["total_tokens"],
            prompt_tokens=llm_result["prompt_tokens"],
            completion_tokens=llm_result["completion_tokens"],
            latency_ms=latency_ms,
            cached=False,
        )

        # Cache response
        await cache.set(cache_key, response.model_dump(), ttl=3600)

        return response

    async def query_stream(
        self,
        query_data: RAGQuery,
    ) -> AsyncGenerator[RAGStreamChunk, None]:
        """Perform streaming RAG query."""
        # Retrieve chunks first
        chunks = await self.search(
            query=query_data.query,
            collection_name=query_data.collection_name,
            top_k=query_data.top_k,
            score_threshold=query_data.score_threshold,
            filters=query_data.filters,
        )

        # Send sources first
        yield RAGStreamChunk(
            type="sources",
            chunks=chunks,
        )

        # Build context
        context = "\n\n---\n\n".join([
            f"Source: {chunk.document_name}\n{chunk.content}"
            for chunk in chunks
        ])

        system_prompt = query_data.system_prompt or """You are a helpful AI assistant. 
Answer the user's question based on the provided context."""

        prompt = f"""Context:
{context}

Question: {query_data.query}

Answer:"""

        # Stream LLM response
        async for text_chunk in llm_service.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=query_data.model,
            temperature=query_data.temperature,
            max_tokens=query_data.max_tokens,
        ):
            yield RAGStreamChunk(type="chunk", content=text_chunk)

        # Send done signal
        yield RAGStreamChunk(type="done")

    async def delete_document_vectors(
        self,
        collection_name: str,
        document_id: str,
    ) -> bool:
        """Delete all vectors for a document."""
        try:
            self.qdrant.delete(
                collection_name=collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(
                                    value=document_id),
                            )
                        ]
                    )
                ),
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to delete document vectors",
                document_id=document_id,
                error=str(e),
            )
            raise
