from typing import Any

from pydantic import BaseModel


class KieWebhookPayload(BaseModel):
    taskId: str | None = None
    status: str | None = None
    code: int | None = None
    job_id: str | None = None
    data: dict[str, Any] | None = None


class KieWebhookResponse(BaseModel):
    accepted: bool
    job_id: str | None = None
    mapped_status: str | None = None
    updated: bool = False
    output_video_url: str | None = None
    output_last_frame_url: str | None = None
    retry_count: int | None = None
    next_retry_at: str | None = None
    dead_lettered: bool | None = None
