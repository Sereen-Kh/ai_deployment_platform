"""API Dependencies for authentication and authorization."""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import verify_token
from api.models.user import User
from api.models.api_key import APIKey

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Security(bearer_scheme)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(credentials.credentials, token_type="access")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == token_data.sub))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_api_key_user(
    api_key: Annotated[Optional[str], Security(api_key_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    """Get user from API key if provided."""
    if not api_key:
        return None

    # Look up API key (hashed)
    from core.security import get_password_hash

    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == get_password_hash(api_key))
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj or not api_key_obj.is_active:
        return None

    # Update last used
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()

    # Get user
    result = await db.execute(select(User).where(User.id == api_key_obj.user_id))
    return result.scalar_one_or_none()


async def get_user_or_api_key(
    jwt_user: Annotated[Optional[User], Depends(get_current_user)],
    api_key_user: Annotated[Optional[User], Depends(get_api_key_user)],
) -> User:
    """Get user from either JWT or API key."""
    user = jwt_user or api_key_user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def require_scopes(required_scopes: list[str]):
    """Dependency factory to require specific scopes."""

    async def check_scopes(
        credentials: Annotated[
            HTTPAuthorizationCredentials, Security(bearer_scheme)
        ],
    ) -> bool:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        token_data = verify_token(credentials.credentials)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Check if user has required scopes
        user_scopes = set(token_data.scopes)
        if not all(scope in user_scopes for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return True

    return Depends(check_scopes)


# Missing import for datetime
