from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings


class FalClient:
    def __init__(self) -> None:
        self.base_url = settings.fal_queue_base_url.rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        api_key = settings.fal_api_key
        if not api_key:
            raise RuntimeError("FAL_API_KEY is not configured.")
        return {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _encoded_endpoint(endpoint_id: str) -> str:
        # Keep slashes because Fal endpoint IDs are path-like IDs.
        return quote(endpoint_id.strip("/"), safe="/")

    async def submit(
        self,
        *,
        endpoint_id: str,
        arguments: dict[str, Any],
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        encoded = self._encoded_endpoint(endpoint_id)
        url = f"{self.base_url}/{encoded}"
        params: dict[str, str] | None = None
        if webhook_url:
            params = {"fal_webhook": webhook_url}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, params=params, json=arguments, headers=self._headers)
            response.raise_for_status()
            return response.json()

    async def status(self, *, endpoint_id: str, request_id: str, with_logs: bool = True) -> dict[str, Any]:
        encoded = self._encoded_endpoint(endpoint_id)
        url = f"{self.base_url}/{encoded}/requests/{request_id}/status"
        params = {"logs": "1"} if with_logs else None
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=self._headers)
            response.raise_for_status()
            return response.json()

    async def result(self, *, endpoint_id: str, request_id: str) -> dict[str, Any]:
        encoded = self._encoded_endpoint(endpoint_id)
        url = f"{self.base_url}/{encoded}/requests/{request_id}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()


fal_client = FalClient()
