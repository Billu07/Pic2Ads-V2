from typing import Any

from pydantic import BaseModel


class FalWebhookPayload(BaseModel):
    request_id: str | None = None
    gateway_request_id: str | None = None
    status: str | None = None
    payload: dict[str, Any] | None = None
    error: str | dict[str, Any] | None = None

    # Backward-compatible aliases for older payload shapes.
    taskId: str | None = None
    job_id: str | None = None
    data: dict[str, Any] | None = None


class FalWebhookResponse(BaseModel):
    accepted: bool
    job_id: str | None = None
    mapped_status: str | None = None
    updated: bool = False
    output_video_url: str | None = None
    output_last_frame_url: str | None = None
    retry_count: int | None = None
    next_retry_at: str | None = None
    dead_lettered: bool | None = None
