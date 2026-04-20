from typing import Any

import httpx

from app.core.config import settings


class KieClient:
    def __init__(self) -> None:
        self.base_url = settings.kie_base_url.rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        if not settings.kie_api_key:
            raise RuntimeError("KIE_API_KEY is not configured.")
        return {
            "Authorization": f"Bearer {settings.kie_api_key}",
            "Content-Type": "application/json",
        }

    async def create_task(self, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{settings.kie_create_task_path}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=body, headers=self._headers)
            response.raise_for_status()
            return response.json()

    async def get_task_detail(self, task_id: str) -> dict[str, Any]:
        url = f"{self.base_url}{settings.kie_task_detail_path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={"taskId": task_id}, headers=self._headers)
            response.raise_for_status()
            return response.json()


kie_client = KieClient()

