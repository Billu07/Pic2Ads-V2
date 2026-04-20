from pydantic import BaseModel, Field


class ProductInput(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    product_image_url: str = Field(min_length=1, max_length=2000)


class DeliverableRequest(BaseModel):
    aspect: str = Field(pattern=r"^(9:16|1:1|16:9)$")
    duration: int = Field(ge=6, le=60)


class CreateJobRequest(BaseModel):
    mode: str = Field(pattern=r"^(ugc|pro_arc|tv)$")
    duration_s: int = Field(ge=10, le=60)
    product: ProductInput
    deliverables: list[DeliverableRequest] = Field(default_factory=list)
    brand_id: str | None = None
    brief: str | None = None


class JobResponse(BaseModel):
    id: str
    status: str
    mode: str
    duration_s: int


class JobStatusResponse(JobResponse):
    created_at: str


class DispatchWorkflowResponse(BaseModel):
    job_id: str
    temporal_workflow_id: str
    temporal_task_queue: str


class LocalPipelineRunResponse(BaseModel):
    job_id: str
    product_intel_status: str
    duration_plan_status: str
    video_generate_status: str
