from pydantic import BaseModel


class ExportSegmentItem(BaseModel):
    unit_id: int
    unit_sequence: int
    unit_pattern: str
    segment_id: int
    segment_order: int
    duration_s: int
    status: str
    prompt_seed: str | None = None
    output_video_url: str | None = None
    output_last_frame_url: str | None = None
    ready: bool = False


class ExportManifestResponse(BaseModel):
    job_id: str
    status: str
    total_units: int
    total_segments: int
    ready_segments: int
    missing_segments: int
    total_duration_s: int
    ready_duration_s: int
    timeline: list[ExportSegmentItem]
