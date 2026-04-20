from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.creative import BrandConstraintsOutput, PersonaOutput
from app.models.product_intel import ProductIntelOutput


class DialogueBeat(BaseModel):
    t_start: float = Field(ge=0)
    t_end: float = Field(gt=0)
    line: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def validate_time_window(self) -> "DialogueBeat":
        if self.t_end <= self.t_start:
            raise ValueError("dialogue beat t_end must be greater than t_start")
        return self


class VisualBeat(BaseModel):
    t_start: float = Field(ge=0)
    t_end: float = Field(gt=0)
    action: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def validate_time_window(self) -> "VisualBeat":
        if self.t_end <= self.t_start:
            raise ValueError("visual beat t_end must be greater than t_start")
        return self


class ScriptVariant(BaseModel):
    variant_id: str = Field(min_length=1, max_length=40)
    angle: str = Field(min_length=1, max_length=80)
    setting: str = Field(min_length=1, max_length=180)
    tone: str = Field(min_length=1, max_length=120)
    filming_method: str = Field(min_length=1, max_length=120)
    first_frame_description: str = Field(min_length=1, max_length=600)
    product_feature_focus: str = Field(min_length=1, max_length=240)
    hook: str = Field(min_length=1, max_length=220)
    render_pattern_hint: Literal["single_gen", "single_take", "two_cuts", "three_cuts", "tv_shotlist"] = (
        "single_gen"
    )
    segment_count_hint: int | None = Field(default=None, ge=1, le=8)
    dialogue_beats: list[DialogueBeat] = Field(min_length=1, max_length=6)
    visual_beats: list[VisualBeat] = Field(min_length=1, max_length=8)
    authenticity_markers: list[str] = Field(min_length=1, max_length=6)


class ScreenwriterInput(BaseModel):
    mode: Literal["ugc", "pro_arc", "tv"]
    duration_s: int = Field(ge=6, le=60)
    product_name: str = Field(min_length=1, max_length=200)
    product_image_url: str = Field(min_length=1, max_length=2000)
    brief: str | None = Field(default=None, max_length=3000)
    product_intel: ProductIntelOutput
    brand_constraints: BrandConstraintsOutput | None = None
    persona: PersonaOutput | None = None


class ScreenwriterOutput(BaseModel):
    mode: Literal["ugc", "pro_arc", "tv"]
    scripts: list[ScriptVariant] = Field(min_length=1, max_length=6)


class ScriptRunResponse(BaseModel):
    job_id: str
    cached: bool
    agent_name: str
    prompt_version: str
    output: ScreenwriterOutput
