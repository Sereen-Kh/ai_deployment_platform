"""HTTP client for inter-service communication."""

import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ServiceClient:
    """HTTP client for microservice communication."""

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize service client.

        Args:
            base_url: Base URL of the target service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make GET request.

        Args:
            path: Request path
            params: Query parameters
            headers: Request headers

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"GET {url} failed: {e}")
            raise

    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make POST request.

        Args:
            path: Request path
            data: Form data
            json: JSON body
            headers: Request headers

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = await self.client.post(
                url,
                data=data,
                json=json,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"POST {url} failed: {e}")
            raise

    async def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make PUT request.

        Args:
            path: Request path
            data: Form data
            json: JSON body
            headers: Request headers

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = await self.client.put(
                url,
                data=data,
                json=json,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"PUT {url} failed: {e}")
            raise

    async def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make DELETE request.

        Args:
            path: Request path
            headers: Request headers

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = await self.client.delete(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"DELETE {url} failed: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
