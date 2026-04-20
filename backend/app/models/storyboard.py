from pydantic import BaseModel, Field, model_validator

from app.models.concepts import TvConcept
from app.models.creative import BrandConstraintsOutput, PersonaOutput
from app.models.prompting import CreativeDecisions
from app.models.product_intel import ProductIntelOutput


class TvStoryboardShot(BaseModel):
    shot_id: str = Field(min_length=1, max_length=80)
    sequence: int = Field(ge=0)
    duration_s: int = Field(ge=1, le=15)
    purpose: str = Field(min_length=1, max_length=240)
    visual_description: str = Field(min_length=1, max_length=700)
    camera_intent: str = Field(min_length=1, max_length=180)
    transition_in: str = Field(default="hard_cut", pattern=r"^(opening|hard_cut|extend_from_previous)$")


class TvStoryboardGenerateInput(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    brief: str | None = Field(default=None, max_length=3000)
    duration_s: int = Field(ge=15, le=60)
    prompt_pack_id: str = Field(min_length=1, max_length=80)
    prompt_directives: list[str] = Field(default_factory=list, max_length=8)
    creative_decisions: CreativeDecisions
    selected_concept: TvConcept
    product_intel: ProductIntelOutput
    brand_constraints: BrandConstraintsOutput
    persona: PersonaOutput


class TvStoryboardGenerateOutput(BaseModel):
    shots: list[TvStoryboardShot] = Field(min_length=3, max_length=12)

    @model_validator(mode="after")
    def validate_order(self) -> "TvStoryboardGenerateOutput":
        for idx, shot in enumerate(self.shots):
            if shot.sequence != idx:
                raise ValueError("storyboard shot sequence must be contiguous and 0-indexed")
        return self


class TvStoryboardGenerateResponse(BaseModel):
    job_id: str
    concept_id: str
    cached: bool
    shots: list[TvStoryboardShot]


class TvStoryboardListResponse(BaseModel):
    job_id: str
    concept_id: str | None = None
    generated: bool
    shots: list[TvStoryboardShot]
