"""HTTP client for AI Platform API."""

from typing import Any, Optional

import httpx
from rich.console import Console

from .config import get_api_key, load_config

console = Console()


class APIClient:
    """HTTP client for interacting with the AI Platform API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        config = load_config()
        self.base_url = (base_url or config.api_url).rstrip("/")
        self.api_key = api_key or get_api_key()
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception:
                error_detail = response.text or str(e)
            raise APIError(
                f"API Error ({response.status_code}): {error_detail}")
        except Exception as e:
            raise APIError(f"Request failed: {e}")

    # Auth endpoints
    def login(self, email: str, password: str) -> dict:
        """Login and get access token."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return self._handle_response(response)

    def register(self, email: str, password: str) -> dict:
        """Register a new user."""
        response = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        return self._handle_response(response)

    # Deployment endpoints
    def list_deployments(self) -> list:
        """List all deployments."""
        response = self.client.get("/api/v1/deployments")
        return self._handle_response(response)

    def get_deployment(self, deployment_id: str) -> dict:
        """Get a specific deployment."""
        response = self.client.get(f"/api/v1/deployments/{deployment_id}")
        return self._handle_response(response)

    def create_deployment(
        self,
        name: str,
        model_name: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> dict:
        """Create a new deployment."""
        response = self.client.post(
            "/api/v1/deployments",
            json={
                "name": name,
                "model_name": model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        return self._handle_response(response)

    def delete_deployment(self, deployment_id: str) -> dict:
        """Delete a deployment."""
        response = self.client.delete(f"/api/v1/deployments/{deployment_id}")
        return self._handle_response(response)

    def start_deployment(self, deployment_id: str) -> dict:
        """Start a deployment."""
        response = self.client.post(
            f"/api/v1/deployments/{deployment_id}/start")
        return self._handle_response(response)

    def stop_deployment(self, deployment_id: str) -> dict:
        """Stop a deployment."""
        response = self.client.post(
            f"/api/v1/deployments/{deployment_id}/stop")
        return self._handle_response(response)

    def invoke_deployment(self, deployment_id: str, prompt: str) -> dict:
        """Invoke a deployment with a prompt."""
        response = self.client.post(
            f"/api/v1/deployments/{deployment_id}/invoke",
            json={"prompt": prompt},
        )
        return self._handle_response(response)

    # RAG endpoints
    def list_collections(self) -> list:
        """List all RAG collections."""
        response = self.client.get("/api/v1/rag/collections")
        return self._handle_response(response)

    def create_collection(self, name: str, description: str = "") -> dict:
        """Create a new RAG collection."""
        response = self.client.post(
            "/api/v1/rag/collections",
            json={"name": name, "description": description},
        )
        return self._handle_response(response)

    def delete_collection(self, collection_id: str) -> dict:
        """Delete a RAG collection."""
        response = self.client.delete(
            f"/api/v1/rag/collections/{collection_id}")
        return self._handle_response(response)

    def upload_document(self, collection_id: str, file_path: str) -> dict:
        """Upload a document to a collection."""
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f)}
            response = self.client.post(
                f"/api/v1/rag/collections/{collection_id}/documents",
                files=files,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return self._handle_response(response)

    def query_collection(
        self, collection_id: str, query: str, top_k: int = 5
    ) -> dict:
        """Query a RAG collection."""
        response = self.client.post(
            f"/api/v1/rag/collections/{collection_id}/query",
            json={"query": query, "top_k": top_k},
        )
        return self._handle_response(response)

    # Analytics endpoints
    def get_dashboard(self) -> dict:
        """Get dashboard analytics."""
        response = self.client.get("/api/v1/analytics/dashboard")
        return self._handle_response(response)

    def get_usage(self, period: str = "7d") -> dict:
        """Get usage analytics."""
        response = self.client.get(f"/api/v1/analytics/usage?period={period}")
        return self._handle_response(response)

    def get_costs(self, period: str = "7d") -> dict:
        """Get cost analytics."""
        response = self.client.get(f"/api/v1/analytics/costs?period={period}")
        return self._handle_response(response)

    # API Key endpoints
    def list_api_keys(self) -> list:
        """List all API keys."""
        response = self.client.get("/api/v1/api-keys")
        return self._handle_response(response)

    def create_api_key(self, name: str) -> dict:
        """Create a new API key."""
        response = self.client.post(
            "/api/v1/api-keys",
            json={"name": name},
        )
        return self._handle_response(response)

    def delete_api_key(self, key_id: str) -> dict:
        """Delete an API key."""
        response = self.client.delete(f"/api/v1/api-keys/{key_id}")
        return self._handle_response(response)

    # Health check
    def health_check(self) -> dict:
        """Check API health."""
        response = self.client.get("/api/v1/health")
        return self._handle_response(response)


class APIError(Exception):
    """API error exception."""
    pass
