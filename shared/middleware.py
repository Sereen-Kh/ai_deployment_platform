"""Shared middleware for FastAPI services."""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
import time
import logging
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

security = HTTPBearer()


async def auth_middleware(
    request: Request,
    call_next: Callable,
    security_manager,
    redis_client=None
):
    """Authentication middleware.

    Args:
        request: FastAPI request
        call_next: Next middleware/route
        security_manager: SecurityManager instance
        redis_client: Optional RedisClient for token blacklist

    Returns:
        Response
    """
    # Skip auth for health and docs endpoints
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Extract token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.replace("Bearer ", "")

    # Check if token is blacklisted (logout)
    if redis_client:
        blacklisted = await redis_client.get(f"blacklist:{token}")
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

    # Verify token
    token_data = security_manager.decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Add user context to request state
    request.state.user_id = token_data.user_id
    request.state.email = token_data.email
    request.state.org_id = token_data.org_id
    request.state.roles = token_data.roles
    request.state.scopes = token_data.scopes

    return await call_next(request)


async def rate_limit_middleware(
    request: Request,
    call_next: Callable,
    redis_client,
    limit: int = 100,
    window: int = 60
):
    """Rate limiting middleware.

    Args:
        request: FastAPI request
        call_next: Next middleware/route
        redis_client: RedisClient instance
        limit: Max requests per window
        window: Time window in seconds

    Returns:
        Response
    """
    # Get identifier (user_id or IP)
    identifier = getattr(request.state, "user_id", None) or request.client.host
    key = f"rate_limit:{identifier}"

    allowed, remaining = await redis_client.rate_limit(key, limit, window)

    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "message": "Rate limit exceeded",
                "retry_after": window
            }
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(window)

    return response


async def metrics_middleware(request: Request, call_next: Callable):
    """Prometheus metrics middleware.

    Args:
        request: FastAPI request
        call_next: Next middleware/route

    Returns:
        Response
    """
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response


async def error_handling_middleware(request: Request, call_next: Callable):
    """Global error handling middleware.

    Args:
        request: FastAPI request
        call_next: Next middleware/route

    Returns:
        Response
    """
    try:
        return await call_next(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e) if logger.level == logging.DEBUG else None
            }
        )
