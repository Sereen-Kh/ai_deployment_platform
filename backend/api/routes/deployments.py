"""Deployment management routes."""

from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.dependencies import get_current_active_user
from api.models.user import User
from api.models.deployment import (
    Deployment,
    DeploymentCreate,
    DeploymentList,
    DeploymentResponse,
    DeploymentStatus,
    DeploymentUpdate,
)
from services.deployment_service import DeploymentService

router = APIRouter()


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment_data: DeploymentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeploymentResponse:
    """Create a new deployment."""
    service = DeploymentService(db)
    deployment = await service.create_deployment(
        user_id=current_user.id,
        data=deployment_data,
    )
    return DeploymentResponse.model_validate(deployment)


@router.get("", response_model=DeploymentList)
async def list_deployments(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[DeploymentStatus] = None,
    search: Optional[str] = None,
) -> DeploymentList:
    """List all deployments for the current user."""
    # Build query
    query = select(Deployment).where(Deployment.user_id == current_user.id)

    if status_filter:
        query = query.where(Deployment.status == status_filter.value)

    if search:
        query = query.where(Deployment.name.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.order_by(Deployment.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    deployments = result.scalars().all()

    return DeploymentList(
        items=[DeploymentResponse.model_validate(d) for d in deployments],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeploymentResponse:
    """Get a specific deployment."""
    result = await db.execute(
        select(Deployment).where(
            Deployment.id == deployment_id,
            Deployment.user_id == current_user.id,
        )
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found",
        )

    return DeploymentResponse.model_validate(deployment)


@router.patch("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: UUID,
    update_data: DeploymentUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeploymentResponse:
    """Update a deployment."""
    result = await db.execute(
        select(Deployment).where(
            Deployment.id == deployment_id,
            Deployment.user_id == current_user.id,
        )
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if field == "config":
            deployment.config = value.model_dump() if hasattr(value, "model_dump") else value
        else:
            setattr(deployment, field, value)

    deployment.version += 1
    await db.commit()
    await db.refresh(deployment)

    return DeploymentResponse.model_validate(deployment)


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a deployment."""
    result = await db.execute(
        select(Deployment).where(
            Deployment.id == deployment_id,
            Deployment.user_id == current_user.id,
        )
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found",
        )

    # Mark as deleted (soft delete)
    deployment.status = DeploymentStatus.DELETED.value
    await db.commit()


@router.post("/{deployment_id}/start", response_model=DeploymentResponse)
async def start_deployment(
    deployment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeploymentResponse:
    """Start a stopped deployment."""
    service = DeploymentService(db)
    deployment = await service.start_deployment(deployment_id, current_user.id)
    return DeploymentResponse.model_validate(deployment)


@router.post("/{deployment_id}/stop", response_model=DeploymentResponse)
async def stop_deployment(
    deployment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeploymentResponse:
    """Stop a running deployment."""
    service = DeploymentService(db)
    deployment = await service.stop_deployment(deployment_id, current_user.id)
    return DeploymentResponse.model_validate(deployment)


@router.post("/{deployment_id}/redeploy", response_model=DeploymentResponse)
async def redeploy(
    deployment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeploymentResponse:
    """Redeploy with current configuration."""
    service = DeploymentService(db)
    deployment = await service.redeploy(deployment_id, current_user.id)
    return DeploymentResponse.model_validate(deployment)
