"""Analytics and metrics routes."""

from datetime import datetime, timedelta
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.dependencies import get_current_active_user
from api.models.user import User

router = APIRouter()


class UsageMetrics(BaseModel):
    """Usage metrics response."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: float
    avg_latency_ms: float
    p95_latency_ms: float
    cache_hit_rate: float


class TimeSeriesPoint(BaseModel):
    """Time series data point."""

    timestamp: datetime
    value: float


class TimeSeriesData(BaseModel):
    """Time series data response."""

    metric_name: str
    data: list[TimeSeriesPoint]
    total: float
    average: float


class DashboardStats(BaseModel):
    """Dashboard overview statistics."""

    total_deployments: int
    active_deployments: int
    total_documents: int
    total_requests_today: int
    total_cost_this_month: float
    api_keys_count: int


class ModelUsage(BaseModel):
    """Model usage breakdown."""

    model: str
    requests: int
    tokens: int
    cost: float
    percentage: float


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStats:
    """Get dashboard overview statistics."""
    # These would be real queries in production
    # For now, return placeholder data
    return DashboardStats(
        total_deployments=12,
        active_deployments=8,
        total_documents=156,
        total_requests_today=1247,
        total_cost_this_month=127.50,
        api_keys_count=3,
    )


@router.get("/usage", response_model=UsageMetrics)
async def get_usage_metrics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    deployment_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    period: str = Query("24h", pattern="^(1h|24h|7d|30d|90d)$"),
) -> UsageMetrics:
    """Get usage metrics for deployments."""
    # Set default date range based on period
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        period_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
        }
        start_date = end_date - period_map.get(period, timedelta(days=1))

    # In production, these would be real aggregated metrics
    return UsageMetrics(
        total_requests=15420,
        successful_requests=15210,
        failed_requests=210,
        total_tokens=2456780,
        prompt_tokens=1842585,
        completion_tokens=614195,
        estimated_cost=49.14,
        avg_latency_ms=234.5,
        p95_latency_ms=890.2,
        cache_hit_rate=0.32,
    )


@router.get("/usage/timeseries", response_model=TimeSeriesData)
async def get_usage_timeseries(
    current_user: Annotated[User, Depends(get_current_active_user)],
    metric: str = Query(..., pattern="^(requests|tokens|cost|latency)$"),
    period: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    deployment_id: Optional[UUID] = None,
) -> TimeSeriesData:
    """Get time series data for a specific metric."""
    # Generate sample time series data
    end_time = datetime.utcnow()

    period_config = {
        "1h": (60, timedelta(minutes=1)),
        "24h": (24, timedelta(hours=1)),
        "7d": (7, timedelta(days=1)),
        "30d": (30, timedelta(days=1)),
    }

    points, interval = period_config.get(period, (24, timedelta(hours=1)))

    import random
    data = []
    for i in range(points):
        timestamp = end_time - (interval * (points - i - 1))
        # Generate realistic-looking values based on metric
        if metric == "requests":
            value = random.randint(50, 200) + random.random() * 50
        elif metric == "tokens":
            value = random.randint(10000, 50000)
        elif metric == "cost":
            value = random.random() * 5 + 1
        else:  # latency
            value = random.randint(100, 500) + random.random() * 100

        data.append(TimeSeriesPoint(
            timestamp=timestamp, value=round(value, 2)))

    values = [p.value for p in data]
    return TimeSeriesData(
        metric_name=metric,
        data=data,
        total=round(sum(values), 2),
        average=round(sum(values) / len(values), 2),
    )


@router.get("/models", response_model=list[ModelUsage])
async def get_model_usage(
    current_user: Annotated[User, Depends(get_current_active_user)],
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
) -> list[ModelUsage]:
    """Get usage breakdown by model."""
    # Sample data - would be real aggregations in production
    total_requests = 15420
    return [
        ModelUsage(
            model="gpt-4-turbo-preview",
            requests=8500,
            tokens=1500000,
            cost=30.00,
            percentage=55.1,
        ),
        ModelUsage(
            model="gpt-3.5-turbo",
            requests=5200,
            tokens=800000,
            cost=8.00,
            percentage=33.7,
        ),
        ModelUsage(
            model="claude-3-opus",
            requests=1720,
            tokens=156780,
            cost=11.14,
            percentage=11.2,
        ),
    ]


@router.get("/costs")
async def get_cost_breakdown(
    current_user: Annotated[User, Depends(get_current_active_user)],
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
) -> dict:
    """Get cost breakdown by category."""
    return {
        "period": period,
        "total_cost": 127.50,
        "breakdown": {
            "llm_inference": 98.50,
            "embeddings": 12.00,
            "storage": 8.00,
            "compute": 9.00,
        },
        "by_deployment": [
            {"name": "Production RAG", "cost": 65.00},
            {"name": "Customer Support Bot", "cost": 42.50},
            {"name": "Internal Search", "cost": 20.00},
        ],
        "trend": {
            "change_percent": 12.5,
            "direction": "up",
        },
    }


@router.get("/errors")
async def get_error_analytics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    period: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    deployment_id: Optional[UUID] = None,
) -> dict:
    """Get error analytics."""
    return {
        "period": period,
        "total_errors": 210,
        "error_rate": 0.0136,
        "by_type": [
            {"type": "rate_limit", "count": 85, "percentage": 40.5},
            {"type": "timeout", "count": 62, "percentage": 29.5},
            {"type": "model_error", "count": 38, "percentage": 18.1},
            {"type": "validation", "count": 25, "percentage": 11.9},
        ],
        "trend": {
            "change_percent": -5.2,
            "direction": "down",
        },
    }
