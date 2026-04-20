from pydantic import BaseModel, Field, model_validator


class SeedanceSubmitRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=20_000)
    duration: int = Field(ge=4, le=15, default=15)
    aspect_ratio: str = Field(default="9:16", pattern=r"^(1:1|4:3|3:4|16:9|9:16|21:9|adaptive)$")
    resolution: str = Field(default="720p", pattern=r"^(480p|720p|1080p)$")
    generate_audio: bool = False
    web_search: bool = False
    nsfw_checker: bool = False

    first_frame_url: str | None = None
    last_frame_url: str | None = None
    reference_image_urls: list[str] = Field(default_factory=list, max_length=9)
    reference_video_urls: list[str] = Field(default_factory=list, max_length=3)
    reference_audio_urls: list[str] = Field(default_factory=list, max_length=3)
    callback_url: str | None = None
    segment_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_mode_exclusivity(self) -> "SeedanceSubmitRequest":
        has_first_last = bool(self.first_frame_url or self.last_frame_url)
        has_multimodal = bool(
            self.reference_image_urls or self.reference_video_urls or self.reference_audio_urls
        )
        if has_first_last and has_multimodal:
            raise ValueError(
                "first_frame_url/last_frame_url cannot be combined with reference_* inputs."
            )
        return self


class SeedanceSubmitResponse(BaseModel):
    job_id: str
    task_id: str
    provider: str
    status: str
    deduped: bool = False


class SeedanceTaskSyncResponse(BaseModel):
    job_id: str
    task_id: str
    provider: str
    provider_status: str | None = None
    mapped_job_status: str | None = None
    updated: bool = False
    output_video_url: str | None = None
    output_last_frame_url: str | None = None
    retry_count: int | None = None
    next_retry_at: str | None = None
    dead_lettered: bool | None = None


class SeedanceRetryRunResponse(BaseModel):
    provider: str = "kie"
    claimed: int = 0
    resubmitted: int = 0
    rescheduled: int = 0
    dead_lettered: int = 0
