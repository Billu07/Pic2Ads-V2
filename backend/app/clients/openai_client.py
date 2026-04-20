import json
from typing import Any

import httpx

from app.core.config import settings
from app.models.creative import (
    BrandConstraintsOutput,
    BrandStrategistInput,
    CastingInput,
    PersonaOutput,
)
from app.models.product_intel import ProductIntelInput, ProductIntelOutput
from app.models.scripts import ScreenwriterInput, ScreenwriterOutput


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

        data = await self._post_responses(body=body, headers=headers)

        parsed = self._extract_json_output(data)
        return ProductIntelOutput.model_validate(parsed)

    async def screenwriter_from_context(self, payload: ScreenwriterInput) -> ScreenwriterOutput:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        schema = ScreenwriterOutput.model_json_schema()
        duration_target = min(15, payload.duration_s) if payload.mode == "ugc" else payload.duration_s
        body: dict[str, Any] = {
            "model": settings.openai_script_model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are the Pic2Ads screenwriter.\n"
                                "Write practical script variants for short ad videos.\n"
                                "Return only JSON matching the schema.\n"
                                "Hard constraints from workflow:\n"
                                "- selfie-style realism and conversational speech\n"
                                "- product fidelity: never alter or invent product facts\n"
                                "- no visible phone, overlays, subtitles, watermarks, or logos in-frame\n"
                                "- natural handheld motion, believable everyday setting\n"
                                "- mention only product features present in product_intel.visible_claims "
                                "or clearly implied by affordances.\n"
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"mode={payload.mode}\n"
                                f"duration_s={duration_target}\n"
                                f"product_name={payload.product_name}\n"
                                f"brief={payload.brief or 'none'}\n"
                                f"product_intel={json.dumps(payload.product_intel.model_dump(), ensure_ascii=True)}\n"
                                f"brand_constraints={json.dumps(payload.brand_constraints.model_dump(), ensure_ascii=True) if payload.brand_constraints else 'none'}\n"
                                f"persona={json.dumps(payload.persona.model_dump(), ensure_ascii=True) if payload.persona else 'none'}\n\n"
                                "Mode-specific output rules:\n"
                                "- mode=ugc: generate exactly 3 variants with ids "
                                "ugc_excited_discovery, ugc_casual_recommendation, ugc_in_the_moment_demo; "
                                "set render_pattern_hint=single_gen.\n"
                                "- mode=pro_arc: generate exactly 1 variant with id pro_arc_master; set "
                                "render_pattern_hint to one of single_take/two_cuts/three_cuts based on story structure.\n"
                                "- mode=tv: generate exactly 1 variant with id tv_master; set "
                                "render_pattern_hint=tv_shotlist and segment_count_hint between 3 and 8.\n"
                                "Each variant must include timed dialogue_beats and visual_beats that fit duration.\n"
                                "Keep lines short and human. Avoid polished ad language.\n"
                            ),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "screenwriter_output",
                    "schema": schema,
                    "strict": True,
                }
            },
            "max_output_tokens": 2200,
        }

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        data = await self._post_responses(body=body, headers=headers)
        parsed = self._extract_json_output(data)
        return ScreenwriterOutput.model_validate(parsed)

    async def brand_constraints_from_context(
        self, payload: BrandStrategistInput
    ) -> BrandConstraintsOutput:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        schema = BrandConstraintsOutput.model_json_schema()
        body: dict[str, Any] = {
            "model": settings.openai_script_model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are a brand strategist for short-form video ads.\n"
                                "Return only JSON matching the provided schema.\n"
                                "Output must be specific and executable.\n"
                                "When brand context is missing, infer safe defaults from product_intel.\n"
                                "Never invent regulated claims. Keep banned_claims strict.\n"
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"mode={payload.mode}\n"
                                f"product_name={payload.product_name}\n"
                                f"brand_id={payload.brand_id or 'none'}\n"
                                f"brief={payload.brief or 'none'}\n"
                                f"product_intel={json.dumps(payload.product_intel.model_dump(), ensure_ascii=True)}"
                            ),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "brand_constraints_output",
                    "schema": schema,
                    "strict": True,
                }
            },
            "max_output_tokens": 1400,
        }
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        data = await self._post_responses(body=body, headers=headers)
        parsed = self._extract_json_output(data)
        return BrandConstraintsOutput.model_validate(parsed)

    async def casting_persona_from_context(self, payload: CastingInput) -> PersonaOutput:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        schema = PersonaOutput.model_json_schema()
        body: dict[str, Any] = {
            "model": settings.openai_script_model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are the casting director for Pic2Ads.\n"
                                "Return one specific creator persona as JSON only.\n"
                                "No scripts, no shot list, no extra commentary.\n"
                                "Avoid stereotypes and generic influencer tropes.\n"
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"mode={payload.mode}\n"
                                f"product_name={payload.product_name}\n"
                                f"brief={payload.brief or 'none'}\n"
                                f"product_intel={json.dumps(payload.product_intel.model_dump(), ensure_ascii=True)}\n"
                                f"brand_constraints={json.dumps(payload.brand_constraints.model_dump(), ensure_ascii=True) if payload.brand_constraints else 'none'}"
                            ),
                        },
                        {"type": "input_image", "image_url": payload.product_image_url},
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "casting_persona_output",
                    "schema": schema,
                    "strict": True,
                }
            },
            "max_output_tokens": 1700,
        }
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        data = await self._post_responses(body=body, headers=headers)
        parsed = self._extract_json_output(data)
        return PersonaOutput.model_validate(parsed)

    async def _post_responses(self, *, body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=80.0) as client:
            response = await client.post(f"{self.base_url}/responses", json=body, headers=headers)
            response.raise_for_status()
            return response.json()

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
