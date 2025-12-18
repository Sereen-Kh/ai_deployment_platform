# Backend Tests

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.anyio
    async def test_health_check(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.anyio
    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness check endpoint."""
        response = await client.get("/api/v1/health/ready")
        assert response.status_code == 200


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.anyio
    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
                "full_name": "Test User"
            }
        )
        assert response.status_code in [200, 201, 400]  # 400 if user exists

    @pytest.mark.anyio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "invalid@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401


class TestDeploymentEndpoints:
    """Test deployment endpoints."""

    @pytest.mark.anyio
    async def test_list_deployments_unauthorized(self, client: AsyncClient):
        """Test listing deployments without auth."""
        response = await client.get("/api/v1/deployments")
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_create_deployment_unauthorized(self, client: AsyncClient):
        """Test creating deployment without auth."""
        response = await client.post(
            "/api/v1/deployments",
            json={
                "name": "Test Deployment",
                "model": "gpt-4"
            }
        )
        assert response.status_code == 401


class TestRAGEndpoints:
    """Test RAG endpoints."""

    @pytest.mark.anyio
    async def test_list_collections_unauthorized(self, client: AsyncClient):
        """Test listing collections without auth."""
        response = await client.get("/api/v1/rag/collections")
        assert response.status_code == 401


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""

    @pytest.mark.anyio
    async def test_dashboard_unauthorized(self, client: AsyncClient):
        """Test dashboard access without auth."""
        response = await client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 401
