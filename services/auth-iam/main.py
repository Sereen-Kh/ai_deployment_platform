"""Auth/IAM Microservice - Authentication and Identity Management."""

import logging
from api import auth, users, organizations, api_keys
from config import settings
from shared.models import HealthResponse
from shared.security import SecurityManager
from shared.redis_client import RedisClient
from shared.database import DatabaseManager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize managers
db_manager = DatabaseManager(settings.DATABASE_URL, echo=settings.DEBUG)
redis_client = RedisClient(settings.REDIS_URL)
security_manager = SecurityManager(
    secret_key=settings.SECRET_KEY,
    access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Auth/IAM service...")
    await redis_client.connect()
    await db_manager.create_tables()
    logger.info("Auth/IAM service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Auth/IAM service...")
    await redis_client.disconnect()
    await db_manager.close()
    logger.info("Auth/IAM service stopped")


app = FastAPI(
    title="Auth/IAM Service",
    description="Authentication and Identity Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(organizations.router,
                   prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(
    api_keys.router, prefix="/api/v1/api-keys", tags=["API Keys"])


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        service="auth-iam",
        version="1.0.0",
        details={
            "database": "connected",
            "redis": "connected" if redis_client.redis else "disconnected"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
