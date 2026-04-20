import json

import httpx

from app.agents.base import Agent
from app.clients.openai_client import openai_client
from app.models.product_intel import ProductIntelInput, ProductIntelOutput


class ProductIntelAgent(Agent[ProductIntelInput, ProductIntelOutput]):
    name = "product_intel"
    prompt_version = "gpt4o-vision-v1"

    async def run(self, payload: ProductIntelInput) -> ProductIntelOutput:
        try:
            return await openai_client.product_intel_from_image(payload)
        except (RuntimeError, httpx.HTTPError, ValueError, json.JSONDecodeError):
            # Keep the pipeline usable in dev when API credentials or provider calls are unavailable.
            return self._heuristic_fallback(payload)

    @staticmethod
    def _heuristic_fallback(payload: ProductIntelInput) -> ProductIntelOutput:
        product_name = payload.product_name.lower()

        if any(word in product_name for word in ("serum", "cream", "cleanser", "moisturizer")):
            category_primary = "beauty"
            category_sub = "skincare"
            affordances = ["apply_on_skin", "daily_routine", "close_up_texture"]
            visible_claims = ["gentle", "hydrating"]
        elif any(word in product_name for word in ("bottle", "drink", "tea", "coffee", "juice")):
            category_primary = "beverage"
            category_sub = "ready_to_drink"
            affordances = ["hold_and_pour", "sip", "tabletop_product_shot"]
            visible_claims = ["refreshing", "daily_use"]
        elif any(word in product_name for word in ("headphone", "speaker", "earbud", "charger")):
            category_primary = "electronics"
            category_sub = "consumer_device"
            affordances = ["hold_in_hand", "demo_usage", "macro_product_shot"]
            visible_claims = ["portable", "high_quality"]
        else:
            category_primary = "general_consumer"
            category_sub = "packaged_product"
            affordances = ["handheld_demo", "tabletop_showcase"]
            visible_claims = ["easy_to_use"]

        return ProductIntelOutput(
            category_primary=category_primary,
            category_sub=category_sub,
            price_tier="mid",
            primary_colors=["neutral", "white"],
            affordances=affordances,
            visible_claims=visible_claims,
            unknowns=[
                "exact_ingredients_or_specs",
                "validated_market_positioning",
                "vision_model_unavailable_fallback",
            ],
        )
