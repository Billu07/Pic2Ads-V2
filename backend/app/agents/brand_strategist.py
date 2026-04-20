import json

import httpx

from app.agents.base import Agent
from app.clients.openai_client import openai_client
from app.models.creative import BrandConstraintsOutput, BrandStrategistInput


class BrandStrategistAgent(Agent[BrandStrategistInput, BrandConstraintsOutput]):
    name = "brand_strategist"
    prompt_version = "openai-brand-v1"

    async def run(self, payload: BrandStrategistInput) -> BrandConstraintsOutput:
        try:
            return await openai_client.brand_constraints_from_context(payload)
        except (RuntimeError, httpx.HTTPError, ValueError, json.JSONDecodeError):
            return self._heuristic_fallback(payload)

    @staticmethod
    def _heuristic_fallback(payload: BrandStrategistInput) -> BrandConstraintsOutput:
        category = payload.product_intel.category_primary.lower()
        colors = payload.product_intel.primary_colors[:]
        defaults = ["#D9D9D9", "#8E8E8E", "#232323"]
        palette_hex: list[str] = []
        for color in colors + defaults:
            if color not in palette_hex:
                palette_hex.append(color)
            if len(palette_hex) >= 4:
                break

        speaking = "friend giving honest advice"
        archetype = "Creator"
        tone = ["direct", "credible", "warm"]
        mandatory = ["product shown in actual use"]
        forbidden_visuals = ["text overlays", "visible phones", "competitor products"]
        banned_claims = ["best ever", "miracle", "changed my life"]

        if category in {"beauty", "skincare"}:
            archetype = "Lover"
            tone = ["clean", "gentle", "confident"]
            mandatory.append("close-up product texture moment")
            banned_claims.extend(["cures acne", "medical-grade guaranteed"])
        elif category in {"beverage", "food"}:
            archetype = "Everyman"
            tone = ["energetic", "casual", "grounded"]
            mandatory.append("real sip or pour action")
            banned_claims.extend(["detox guarantee", "instant body transformation"])
        elif category in {"electronics", "consumer_device"}:
            archetype = "Sage"
            speaking = "expert addressing peers"
            tone = ["clear", "practical", "focused"]
            mandatory.append("one practical feature demonstration")

        if payload.brief:
            lowered = payload.brief.lower()
            if "premium" in lowered or "luxury" in lowered:
                archetype = "Ruler"
                tone = ["refined", "assured", "minimal"]
            if "playful" in lowered or "fun" in lowered:
                archetype = "Jester"
                tone = ["light", "playful", "approachable"]

        return BrandConstraintsOutput(
            archetype=archetype,
            tone_descriptors=tone[:5],
            speaking_stance=speaking,
            preferred_terms=[],
            forbidden_terms=["guys", "everyone needs this"],
            banned_claims=banned_claims[:10],
            palette_hex=palette_hex[:6],
            logo_placement="packaging_only",
            forbidden_visual_elements=forbidden_visuals[:8],
            mandatory_elements=mandatory[:8],
            optional_ctas=["See how it fits your routine", "Try it in your daily flow"],
        )


brand_strategist_agent = BrandStrategistAgent()

