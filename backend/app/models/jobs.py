from pydantic import BaseModel, Field

from app.models.prompting import CreativeDecisionsInput


class ProductInput(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    product_image_url: str = Field(min_length=1, max_length=2000)


class DeliverableRequest(BaseModel):
    aspect: str = Field(pattern=r"^(9:16|1:1|16:9)$")
    duration: int = Field(ge=6, le=60)


class CreateJobRequest(BaseModel):
    mode: str = Field(pattern=r"^(ugc|pro_arc|tv)$")
    language: str = Field(default="en", pattern=r"^(en|bn|hi|es)$")
    duration_s: int = Field(ge=10, le=60)
    product: ProductInput
    deliverables: list[DeliverableRequest] = Field(default_factory=list)
    brand_id: str | None = None
    brief: str | None = None
    creative_decisions: CreativeDecisionsInput | None = None


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
    brand_strategy_status: str
    casting_status: str
    script_status: str
    tv_gate_status: str
    duration_plan_status: str
    video_generate_status: str


class LocalPipelineRunRequest(BaseModel):
    generate_audio: bool = True
    render_all_variants: bool = False
    selected_variant_id: str | None = Field(default=None, max_length=80)


class TvConceptSelectRequest(BaseModel):
    concept_id: str = Field(min_length=1, max_length=120)


class TvConceptSelectResponse(BaseModel):
    job_id: str
    concept_id: str
    concept_selected: bool
    storyboard_generated: bool
    storyboard_approved: bool
    ready_for_render: bool


class TvStoryboardApproveRequest(BaseModel):
    approved: bool = True


class TvStoryboardApproveResponse(BaseModel):
    job_id: str
    storyboard_generated: bool
    storyboard_approved: bool
    concept_selected: bool
    ready_for_render: bool


class TvGateStatusResponse(BaseModel):
    job_id: str
    required: bool
    concept_selected: bool
    selected_concept_id: str | None = None
    storyboard_generated: bool
    storyboard_approved: bool
    ready_for_render: bool
