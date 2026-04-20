from typing import Literal

from pydantic import BaseModel, Field, field_validator


CreativeHookStyle = Literal[
    "problem_first",
    "social_proof",
    "demo_first",
    "storytime_confession",
    "authority_insight",
]

CreativeOfferAngle = Literal[
    "speed_convenience",
    "premium_quality",
    "value_savings",
    "emotional_relief",
    "performance_proof",
]

CreativeCtaStyle = Literal[
    "soft_invite",
    "direct_command",
    "question_prompt",
    "urgency_push",
]


class CreativeDecisions(BaseModel):
    tone: str = Field(min_length=1, max_length=120)
    hook_style: CreativeHookStyle
    offer_angle: CreativeOfferAngle
    cta_style: CreativeCtaStyle
    must_include: list[str] = Field(default_factory=list, max_length=6)
    must_avoid: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("tone", mode="before")
    @classmethod
    def normalize_tone(cls, value: str) -> str:
        return str(value).strip()

    @field_validator("must_include", "must_avoid", mode="before")
    @classmethod
    def normalize_lists(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        cleaned: list[str] = []
        for item in value:
            text = str(item).strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned[:6]


class CreativeDecisionsInput(BaseModel):
    tone: str | None = Field(default=None, max_length=120)
    hook_style: CreativeHookStyle | None = None
    offer_angle: CreativeOfferAngle | None = None
    cta_style: CreativeCtaStyle | None = None
    must_include: list[str] | None = Field(default=None, max_length=6)
    must_avoid: list[str] | None = Field(default=None, max_length=6)

    @field_validator("tone", mode="before")
    @classmethod
    def normalize_optional_tone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None

    @field_validator("must_include", "must_avoid", mode="before")
    @classmethod
    def normalize_optional_lists(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        for item in value:
            text = str(item).strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned[:6]


class PromptPackSpec(BaseModel):
    pack_id: str = Field(min_length=1, max_length=80)
    mode: Literal["ugc", "pro_arc", "tv"]
    script_directives: list[str] = Field(default_factory=list, max_length=8)
    concept_directives: list[str] = Field(default_factory=list, max_length=8)
    storyboard_directives: list[str] = Field(default_factory=list, max_length=8)


class CreativeDecisionsResponse(BaseModel):
    job_id: str
    mode: Literal["ugc", "pro_arc", "tv"]
    prompt_pack_id: str
    decisions: CreativeDecisions
