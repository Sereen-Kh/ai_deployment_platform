"""API Routes module."""

from fastapi import APIRouter

from .auth import router as auth_router
from .deployments import router as deployments_router
from .rag import router as rag_router
from .analytics import router as analytics_router
from .health import router as health_router

# Main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(
    deployments_router, prefix="/deployments", tags=["Deployments"])
api_router.include_router(rag_router, prefix="/rag", tags=["RAG"])
api_router.include_router(
    analytics_router, prefix="/analytics", tags=["Analytics"])
