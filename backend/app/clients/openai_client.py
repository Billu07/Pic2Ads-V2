import json
from typing import Any

import httpx

from app.core.config import settings
from app.models.product_intel import ProductIntelInput, ProductIntelOutput


class OpenAIClient:
    def __init__(self) -> None:
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.openai_vision_model

    async def product_intel_from_image(self, payload: ProductIntelInput) -> ProductIntelOutput:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        schema = ProductIntelOutput.model_json_schema()
        prompt = (
            "You are a product intelligence extractor for ad generation.\n"
            "Return strictly the JSON schema requested.\n"
            "Only include claims clearly visible from the product image or name.\n"
            "If unsure, put the item into `unknowns`."
        )

        body: dict[str, Any] = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"{prompt}\n\n"
                                f"Product name: {payload.product_name}\n"
                                "Extract category, likely price tier, visible cues, and affordances."
                            ),
                        },
                        {"type": "input_image", "image_url": payload.product_image_url},
                    ],
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "product_intel_output",
                    "schema": schema,
                    "strict": True,
                }
            },
            "max_output_tokens": 700,
        }

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/responses", json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

        parsed = self._extract_json_output(data)
        return ProductIntelOutput.model_validate(parsed)

    @staticmethod
    def _extract_json_output(response_json: dict[str, Any]) -> dict[str, Any]:
        output_text = response_json.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return json.loads(output_text)

        output = response_json.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        text = part.get("text")
                        if isinstance(text, str) and text.strip():
                            return json.loads(text)

        raise RuntimeError("OpenAI response did not contain parseable JSON output.")


openai_client = OpenAIClient()

