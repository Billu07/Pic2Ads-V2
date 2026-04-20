from enum import Enum

from pydantic import BaseModel, Field


class RenderPattern(str, Enum):
    SINGLE_GEN = "single_gen"
    EXTEND_CHAIN = "extend_chain"
    CUT_CHAIN = "cut_chain"


class Segment(BaseModel):
    order: int = Field(ge=0)
    duration_s: int = Field(ge=1, le=15)
    prompt_seed: str = Field(min_length=1)


class RenderUnit(BaseModel):
    sequence: int = Field(ge=0)
    pattern: RenderPattern
    total_duration_s: int = Field(ge=1)
    segments: list[Segment]
