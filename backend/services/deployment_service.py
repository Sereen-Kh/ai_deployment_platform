"""Deployment management service."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.deployment import (
    Deployment,
    DeploymentCreate,
    DeploymentStatus,
)


class DeploymentService:
    """Service for managing deployments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deployment(
        self,
        user_id: UUID,
        data: DeploymentCreate,
    ) -> Deployment:
        """Create a new deployment."""
        deployment = Deployment(
            name=data.name,
            description=data.description,
            user_id=user_id,
            deployment_type=data.deployment_type.value,
            status=DeploymentStatus.PENDING.value,
            config=data.config.model_dump(),
            replicas=data.replicas,
            cpu_limit=data.cpu_limit,
            memory_limit=data.memory_limit,
        )

        self.db.add(deployment)
        await self.db.commit()
        await self.db.refresh(deployment)

        # Trigger async deployment task
        # In production, this would queue a Celery task
        # from workers.tasks import deploy_task
        # deploy_task.delay(str(deployment.id))

        return deployment

    async def get_deployment(
        self,
        deployment_id: UUID,
        user_id: UUID,
    ) -> Optional[Deployment]:
        """Get a deployment by ID."""
        result = await self.db.execute(
            select(Deployment).where(
                Deployment.id == deployment_id,
                Deployment.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_deployment_or_404(
        self,
        deployment_id: UUID,
        user_id: UUID,
    ) -> Deployment:
        """Get deployment or raise 404."""
        deployment = await self.get_deployment(deployment_id, user_id)
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found",
            )
        return deployment

    async def start_deployment(
        self,
        deployment_id: UUID,
        user_id: UUID,
    ) -> Deployment:
        """Start a stopped deployment."""
        deployment = await self._get_deployment_or_404(deployment_id, user_id)

        if deployment.status not in [
            DeploymentStatus.STOPPED.value,
            DeploymentStatus.FAILED.value,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start deployment in {deployment.status} state",
            )

        deployment.status = DeploymentStatus.DEPLOYING.value
        deployment.error_message = None
        await self.db.commit()
        await self.db.refresh(deployment)

        # Trigger deployment task
        # deploy_task.delay(str(deployment.id))

        return deployment

    async def stop_deployment(
        self,
        deployment_id: UUID,
        user_id: UUID,
    ) -> Deployment:
        """Stop a running deployment."""
        deployment = await self._get_deployment_or_404(deployment_id, user_id)

        if deployment.status != DeploymentStatus.RUNNING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot stop deployment in {deployment.status} state",
            )

        deployment.status = DeploymentStatus.STOPPED.value
        await self.db.commit()
        await self.db.refresh(deployment)

        # Trigger stop task
        # stop_deployment_task.delay(str(deployment.id))

        return deployment

    async def redeploy(
        self,
        deployment_id: UUID,
        user_id: UUID,
    ) -> Deployment:
        """Redeploy with current configuration."""
        deployment = await self._get_deployment_or_404(deployment_id, user_id)

        deployment.status = DeploymentStatus.DEPLOYING.value
        deployment.version += 1
        deployment.error_message = None
        await self.db.commit()
        await self.db.refresh(deployment)

        # Trigger deployment task
        # deploy_task.delay(str(deployment.id))

        return deployment

    async def update_status(
        self,
        deployment_id: UUID,
        status: DeploymentStatus,
        error_message: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ) -> Deployment:
        """Update deployment status (called by workers)."""
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        deployment.status = status.value
        deployment.error_message = error_message

        if endpoint_url:
            deployment.endpoint_url = endpoint_url

        if status == DeploymentStatus.RUNNING:
            deployment.deployed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(deployment)

        return deployment
