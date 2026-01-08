#!/usr/bin/env python3
"""
Seed script to populate the database with mock/demo data.

Usage:
    cd backend
    python -m scripts.seed_data

This will create:
    - 1 demo user (demo@example.com / password123)
    - 8 sample deployments with various statuses
"""

from api.models.deployment import Deployment, DeploymentStatus, DeploymentType
from api.models.user import User
from core.security import get_password_hash
from core.database import AsyncSessionLocal, init_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# MOCK DATA DEFINITIONS
# =============================================================================

DEMO_USER = {
    "email": "demo@example.com",
    "password": "password123",
    "full_name": "Demo User",
    "is_active": True,
    "is_verified": True,
    "role": "admin",
}

SAMPLE_DEPLOYMENTS = [
    {
        "name": "fraud-detection-prod",
        "description": "Production fraud detection model for payment processing",
        "deployment_type": DeploymentType.RAG.value,
        "status": DeploymentStatus.RUNNING.value,
        "endpoint_url": "https://api.ai-platform.com/v1/fraud-detection",
        "replicas": 3,
        "cpu_limit": "2000m",
        "memory_limit": "4Gi",
        "version": 3,
        "config": {
            "model": {
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "temperature": 0.3,
                "max_tokens": 2048,
            },
            "environment_variables": {"ENV": "production", "LOG_LEVEL": "INFO"},
            "enable_streaming": True,
            "enable_caching": True,
            "cache_ttl": 3600,
        },
    },
    {
        "name": "support-bot-prod",
        "description": "Customer support chatbot for help desk",
        "deployment_type": DeploymentType.CHAT.value,
        "status": DeploymentStatus.RUNNING.value,
        "endpoint_url": "https://api.ai-platform.com/v1/support-bot",
        "replicas": 2,
        "cpu_limit": "1000m",
        "memory_limit": "2Gi",
        "version": 5,
        "config": {
            "model": {
                "provider": "anthropic",
                "model": "claude-3-sonnet-20240229",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "environment_variables": {"ENV": "production"},
            "enable_streaming": True,
            "enable_caching": False,
        },
    },
    {
        "name": "document-qa-staging",
        "description": "Document Q&A system for internal knowledge base",
        "deployment_type": DeploymentType.RAG.value,
        "status": DeploymentStatus.RUNNING.value,
        "endpoint_url": "https://staging.ai-platform.com/v1/doc-qa",
        "replicas": 1,
        "cpu_limit": "1000m",
        "memory_limit": "2Gi",
        "version": 2,
        "config": {
            "model": {
                "provider": "gemini",
                "model": "gemini-1.5-flash",
                "temperature": 0.5,
                "max_tokens": 8192,
            },
            "rag": {
                "collection_name": "internal_docs",
                "top_k": 5,
                "score_threshold": 0.7,
            },
            "environment_variables": {"ENV": "staging"},
            "enable_streaming": True,
            "enable_caching": True,
        },
    },
    {
        "name": "code-assistant-dev",
        "description": "AI coding assistant for developers",
        "deployment_type": DeploymentType.COMPLETION.value,
        "status": DeploymentStatus.STOPPED.value,
        "endpoint_url": None,
        "replicas": 1,
        "cpu_limit": "500m",
        "memory_limit": "1Gi",
        "version": 1,
        "config": {
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.2,
                "max_tokens": 4096,
            },
            "environment_variables": {"ENV": "development"},
            "enable_streaming": True,
            "enable_caching": False,
        },
    },
    {
        "name": "sentiment-analyzer-prod",
        "description": "Real-time sentiment analysis for social media",
        "deployment_type": DeploymentType.CUSTOM.value,
        "status": DeploymentStatus.RUNNING.value,
        "endpoint_url": "https://api.ai-platform.com/v1/sentiment",
        "replicas": 4,
        "cpu_limit": "1500m",
        "memory_limit": "3Gi",
        "version": 7,
        "config": {
            "model": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.0,
                "max_tokens": 256,
            },
            "environment_variables": {"ENV": "production", "BATCH_SIZE": "100"},
            "enable_streaming": False,
            "enable_caching": True,
            "cache_ttl": 7200,
        },
    },
    {
        "name": "translation-service-prod",
        "description": "Multi-language translation API",
        "deployment_type": DeploymentType.COMPLETION.value,
        "status": DeploymentStatus.FAILED.value,
        "endpoint_url": "https://api.ai-platform.com/v1/translate",
        "replicas": 2,
        "cpu_limit": "1000m",
        "memory_limit": "2Gi",
        "version": 4,
        "error_message": "Model loading timeout after 3 retries",
        "config": {
            "model": {
                "provider": "gemini",
                "model": "gemini-1.5-pro",
                "temperature": 0.3,
                "max_tokens": 2048,
            },
            "environment_variables": {"ENV": "production"},
            "enable_streaming": True,
            "enable_caching": True,
        },
    },
    {
        "name": "content-moderator-staging",
        "description": "Content moderation for user-generated content",
        "deployment_type": DeploymentType.CUSTOM.value,
        "status": DeploymentStatus.DEPLOYING.value,
        "endpoint_url": None,
        "replicas": 1,
        "cpu_limit": "1000m",
        "memory_limit": "2Gi",
        "version": 1,
        "config": {
            "model": {
                "provider": "anthropic",
                "model": "claude-3-haiku-20240307",
                "temperature": 0.0,
                "max_tokens": 512,
            },
            "environment_variables": {"ENV": "staging"},
            "enable_streaming": False,
            "enable_caching": False,
        },
    },
    {
        "name": "research-agent-dev",
        "description": "Autonomous research agent for data gathering",
        "deployment_type": DeploymentType.AGENT.value,
        "status": DeploymentStatus.PENDING.value,
        "endpoint_url": None,
        "replicas": 1,
        "cpu_limit": "2000m",
        "memory_limit": "4Gi",
        "version": 1,
        "config": {
            "model": {
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "max_tokens": 8192,
            },
            "environment_variables": {"ENV": "development"},
            "enable_streaming": True,
            "enable_caching": False,
        },
    },
]


# =============================================================================
# SEED FUNCTIONS
# =============================================================================

async def create_demo_user(session: AsyncSession) -> User:
    """Create or get the demo user."""
    # Check if user exists
    result = await session.execute(
        select(User).where(User.email == DEMO_USER["email"])
    )
    user = result.scalar_one_or_none()

    if user:
        print(f"✓ Demo user already exists: {DEMO_USER['email']}")
        return user

    # Create new user
    user = User(
        id=uuid4(),
        email=DEMO_USER["email"],
        hashed_password=get_password_hash(DEMO_USER["password"]),
        full_name=DEMO_USER["full_name"],
        is_active=DEMO_USER["is_active"],
        is_verified=DEMO_USER["is_verified"],
        role=DEMO_USER["role"],
    )
    session.add(user)
    await session.flush()
    print(
        f"✓ Created demo user: {DEMO_USER['email']} (password: {DEMO_USER['password']})")
    return user


async def create_sample_deployments(session: AsyncSession, user: User) -> list[Deployment]:
    """Create sample deployments for the demo user."""
    # Check existing deployments
    result = await session.execute(
        select(Deployment).where(Deployment.user_id == user.id)
    )
    existing = result.scalars().all()

    if existing:
        print(f"✓ {len(existing)} deployments already exist for demo user")
        return list(existing)

    deployments = []
    now = datetime.now(timezone.utc)

    for i, data in enumerate(SAMPLE_DEPLOYMENTS):
        # Stagger created_at times
        created_at = now - timedelta(days=30 - i * 3, hours=i * 2)
        updated_at = now - timedelta(hours=i * 4)
        deployed_at = updated_at if data["status"] == DeploymentStatus.RUNNING.value else None

        deployment = Deployment(
            id=uuid4(),
            name=data["name"],
            description=data["description"],
            user_id=user.id,
            deployment_type=data["deployment_type"],
            status=data["status"],
            config=data["config"],
            replicas=data["replicas"],
            cpu_limit=data["cpu_limit"],
            memory_limit=data["memory_limit"],
            endpoint_url=data["endpoint_url"],
            version=data["version"],
            error_message=data.get("error_message"),
            created_at=created_at,
            updated_at=updated_at,
            deployed_at=deployed_at,
        )
        session.add(deployment)
        deployments.append(deployment)
        print(f"  + {data['name']} ({data['status']})")

    await session.flush()
    print(f"✓ Created {len(deployments)} sample deployments")
    return deployments


async def seed_database():
    """Main seed function."""
    print("\n" + "=" * 60)
    print("  AI Deployment Platform - Database Seeder")
    print("=" * 60 + "\n")

    # Initialize database tables
    print("Initializing database tables...")
    await init_db()
    print("✓ Database tables ready\n")

    async with AsyncSessionLocal() as session:
        try:
            # Create demo user
            user = await create_demo_user(session)

            # Create sample deployments
            print("\nCreating sample deployments...")
            await create_sample_deployments(session, user)

            # Commit all changes
            await session.commit()

            print("\n" + "=" * 60)
            print("  Seeding complete!")
            print("=" * 60)
            print(f"\n  Login credentials:")
            print(f"    Email:    {DEMO_USER['email']}")
            print(f"    Password: {DEMO_USER['password']}")
            print("\n")

        except Exception as e:
            await session.rollback()
            print(f"\n✗ Error during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
