from pydantic import BaseModel, Field, model_validator


class SegmentCreateRequest(BaseModel):
    order: int = Field(ge=0)
    duration_s: int = Field(ge=1, le=15)
    prompt_seed: str | None = Field(default=None, max_length=2000)


class RenderUnitCreateRequest(BaseModel):
    sequence: int = Field(ge=0)
    pattern: str = Field(pattern=r"^(single_gen|extend_chain|cut_chain)$")
    duration_s: int = Field(ge=1, le=120)
    segments: list[SegmentCreateRequest] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_durations(self) -> "RenderUnitCreateRequest":
        total = sum(s.duration_s for s in self.segments)
        if abs(total - self.duration_s) > 1:
            raise ValueError("sum(segments.duration_s) must match duration_s within ±1s.")
        return self


class SegmentResponse(BaseModel):
    id: int
    order: int
    duration_s: int
    prompt_seed: str | None = None
    status: str
    output_video_url: str | None = None
    output_last_frame_url: str | None = None


class RenderUnitResponse(BaseModel):
    id: int
    sequence: int
    pattern: str
    duration_s: int
    segments: list[SegmentResponse]


class RenderUnitListResponse(BaseModel):
    job_id: str
    units: list[RenderUnitResponse]


class SegmentRegenRequest(BaseModel):
    prompt_seed: str | None = Field(default=None, max_length=2000)
    clear_outputs: bool = True


class SegmentRegenResponse(BaseModel):
    job_id: str
    segment: SegmentResponse
