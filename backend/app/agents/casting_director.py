import json
from typing import Literal

import httpx

from app.agents.base import Agent
from app.clients.openai_client import openai_client
from app.models.creative import CastingInput, PersonaOutput


class CastingDirectorAgent(Agent[CastingInput, PersonaOutput]):
    name = "casting_director"
    prompt_version = "openai-casting-v1"

    async def run(self, payload: CastingInput) -> PersonaOutput:
        try:
            return await openai_client.casting_persona_from_context(payload)
        except (RuntimeError, httpx.HTTPError, ValueError, json.JSONDecodeError):
            return self._heuristic_fallback(payload)

    @staticmethod
    def _heuristic_fallback(payload: CastingInput) -> PersonaOutput:
        brief = (payload.brief or "").lower()
        category = payload.product_intel.category_primary.lower()

        name = "Maya Rahman"
        age = 29
        gender: Literal["female", "male", "nonbinary"] = "female"
        occupation = "content strategist"
        location_descriptor = "apartment in a dense city neighborhood"
        style = "clean casual basics with one signature accessory"
        demeanor = "friendly, focused, and naturally expressive"
        speaking_style = "short conversational lines with occasional filler words"
        hobbies = ["morning walks", "meal prep", "short-form content creation"]
        values = ["consistency", "clarity", "practical self-care"]
        pain_points = ["time pressure", "decision fatigue", "inconsistent routines"]
        home = "bright kitchen and compact bathroom with real daily clutter"
        why = (
            "She feels credible for practical daily-product recommendations and naturally fits "
            "selfie-style short videos."
        )

        if "male" in brief:
            name = "Arif Hasan"
            gender = "male"
        elif "nonbinary" in brief:
            name = "Rin Dutta"
            gender = "nonbinary"

        if category in {"electronics", "consumer_device"}:
            occupation = "product designer"
            speaking_style = "clear and practical with direct feature mentions"
            values = ["utility", "reliability", "clean execution"]
        elif category in {"beverage", "food"}:
            occupation = "freelance creative"
            hobbies = ["recipe experiments", "quick workout breaks", "city walks"]
            pain_points = ["afternoon energy dips", "busy schedule", "skipping routines"]

        if "premium" in brief or "luxury" in brief:
            style = "minimal monochrome outfit with polished details"
            demeanor = "calm, assured, and understated"

        return PersonaOutput(
            name=name,
            age=age,
            gender=gender,
            location_descriptor=location_descriptor,
            occupation=occupation,
            appearance="expressive eyes, natural skin texture, and understated everyday styling",
            hair="neatly styled with slight natural flyaways",
            clothing_aesthetic=style,
            signature_details=["small hoop earrings", "thin bracelet", "neutral-toned nails"],
            traits=["observant", "honest", "warm", "practical", "self-aware"],
            demeanor=demeanor,
            speaking_style=speaking_style,
            hobbies=hobbies,
            values=values,
            pain_points=pain_points,
            home_environment=home,
            why_this_person=why,
        )


casting_director_agent = CastingDirectorAgent()
