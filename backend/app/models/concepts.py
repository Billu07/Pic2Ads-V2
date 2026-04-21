from pydantic import BaseModel, Field

from app.models.creative import BrandConstraintsOutput, PersonaOutput
from app.models.prompting import CreativeDecisions
from app.models.product_intel import ProductIntelOutput


class TvConcept(BaseModel):
    concept_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=120)
    logline: str = Field(min_length=1, max_length=240)
    treatment: str = Field(min_length=1, max_length=1400)
    audience_angle: str = Field(min_length=1, max_length=240)
    style_notes: list[str] = Field(min_length=2, max_length=6)


class TvConceptGenerateInput(BaseModel):
    language_code: str = Field(default="en", pattern=r"^(en|bn|hi|es)$")
    language_name: str = Field(default="English", min_length=2, max_length=40)
    product_name: str = Field(min_length=1, max_length=200)
    brief: str | None = Field(default=None, max_length=3000)
    duration_s: int = Field(ge=15, le=60)
    prompt_pack_id: str = Field(min_length=1, max_length=80)
    prompt_directives: list[str] = Field(default_factory=list, max_length=8)
    creative_decisions: CreativeDecisions
    product_intel: ProductIntelOutput
    brand_constraints: BrandConstraintsOutput
    persona: PersonaOutput


class TvConceptGenerateOutput(BaseModel):
    concepts: list[TvConcept] = Field(min_length=3, max_length=3)


class TvConceptGenerateResponse(BaseModel):
    job_id: str
    cached: bool
    concepts: list[TvConcept]


class TvConceptListResponse(BaseModel):
    job_id: str
    generated: bool
    concepts: list[TvConcept]
