from typing import Literal

from pydantic import BaseModel, Field

from app.models.product_intel import ProductIntelOutput


BrandArchetype = Literal[
    "Sage",
    "Hero",
    "Outlaw",
    "Explorer",
    "Creator",
    "Caregiver",
    "Everyman",
    "Innocent",
    "Lover",
    "Jester",
    "Magician",
    "Ruler",
]

BrandSpeakingStance = Literal[
    "expert addressing peers",
    "friend giving honest advice",
    "confident coach",
    "curious guide",
    "irreverent insider",
]


class BrandStrategistInput(BaseModel):
    mode: Literal["ugc", "pro_arc", "tv"]
    product_name: str = Field(min_length=1, max_length=200)
    brief: str | None = Field(default=None, max_length=3000)
    brand_id: str | None = Field(default=None, max_length=120)
    product_intel: ProductIntelOutput


class BrandConstraintsOutput(BaseModel):
    archetype: BrandArchetype
    tone_descriptors: list[str] = Field(min_length=3, max_length=5)
    speaking_stance: BrandSpeakingStance
    preferred_terms: list[str] = Field(default_factory=list, max_length=8)
    forbidden_terms: list[str] = Field(default_factory=list, max_length=8)
    banned_claims: list[str] = Field(default_factory=list, max_length=10)
    palette_hex: list[str] = Field(default_factory=list, max_length=6)
    logo_placement: Literal["end_card", "packaging_only", "lower_third", "none"] = "packaging_only"
    forbidden_visual_elements: list[str] = Field(default_factory=list, max_length=8)
    mandatory_elements: list[str] = Field(default_factory=list, max_length=8)
    optional_ctas: list[str] = Field(default_factory=list, max_length=8)


class BrandStrategistRunResponse(BaseModel):
    job_id: str
    cached: bool
    agent_name: str
    prompt_version: str
    output: BrandConstraintsOutput


class CastingInput(BaseModel):
    mode: Literal["ugc", "pro_arc", "tv"]
    product_name: str = Field(min_length=1, max_length=200)
    brief: str | None = Field(default=None, max_length=3000)
    product_image_url: str = Field(min_length=1, max_length=2000)
    product_intel: ProductIntelOutput
    brand_constraints: BrandConstraintsOutput | None = None


class PersonaOutput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=16, le=90)
    gender: Literal["female", "male", "nonbinary"]
    location_descriptor: str = Field(min_length=1, max_length=200)
    occupation: str = Field(min_length=1, max_length=120)
    appearance: str = Field(min_length=1, max_length=500)
    hair: str = Field(min_length=1, max_length=180)
    clothing_aesthetic: str = Field(min_length=1, max_length=180)
    signature_details: list[str] = Field(min_length=2, max_length=4)
    traits: list[str] = Field(min_length=5, max_length=7)
    demeanor: str = Field(min_length=1, max_length=160)
    speaking_style: str = Field(min_length=1, max_length=180)
    hobbies: list[str] = Field(min_length=3, max_length=5)
    values: list[str] = Field(min_length=3, max_length=5)
    pain_points: list[str] = Field(min_length=3, max_length=5)
    home_environment: str = Field(min_length=1, max_length=240)
    why_this_person: str = Field(min_length=1, max_length=320)


class CastingRunResponse(BaseModel):
    job_id: str
    cached: bool
    agent_name: str
    prompt_version: str
    output: PersonaOutput

