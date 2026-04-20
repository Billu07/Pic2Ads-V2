from fastapi import APIRouter, HTTPException
from psycopg import Error as PsycopgError

from app.core.config import settings
from app.services.brand_strategy import brand_strategy_service
from app.services.casting import casting_service
from app.models.jobs import (
    CreateJobRequest,
    DispatchWorkflowResponse,
    JobResponse,
    JobStatusResponse,
    LocalPipelineRunResponse,
    TvConceptSelectRequest,
    TvConceptSelectResponse,
    TvGateStatusResponse,
    TvStoryboardApproveRequest,
    TvStoryboardApproveResponse,
)
from app.services.duration_planner import duration_planner_service
from app.services.jobs import job_service
from app.services.product_intel import product_intel_service
from app.services.render_units import render_unit_service
from app.services.seedance_pipeline import seedance_pipeline_service
from app.services.scripts import script_service

router = APIRouter(prefix="/jobs")


@router.post("", response_model=JobResponse)
def create_job(req: CreateJobRequest) -> JobResponse:
    try:
        created = job_service.create_job(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_write_failed") from exc

    return JobResponse(
        id=created.id,
        status=created.status,
        mode=created.mode,
        duration_s=created.duration_s,
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str) -> JobStatusResponse:
    try:
        found = job_service.get_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc

    if found is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return found


@router.post("/{job_id}/dispatch", response_model=DispatchWorkflowResponse)
async def dispatch_job(job_id: str) -> DispatchWorkflowResponse:
    try:
        found = job_service.get_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc

    if found is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    try:
        from app.temporal.dispatcher import dispatch_generate_ad
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Temporal runtime is not installed for the current Python interpreter. "
                "Use Python 3.11/3.12 with temporalio to enable dispatch."
            ),
        ) from exc

    try:
        workflow_id = await dispatch_generate_ad(job_id=found.id, mode=found.mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="temporal_dispatch_failed") from exc

    try:
        job_service.mark_running(found.id)
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_status_update_failed") from exc

    return DispatchWorkflowResponse(
        job_id=found.id,
        temporal_workflow_id=workflow_id,
        temporal_task_queue=settings.temporal_task_queue,
    )


@router.post("/{job_id}/pipeline/run-local", response_model=LocalPipelineRunResponse)
async def run_local_pipeline(job_id: str) -> LocalPipelineRunResponse:
    try:
        found = job_service.get_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc
    if found is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    intel = await product_intel_service.run_for_job(job_id)
    if intel is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    brand = await brand_strategy_service.run_for_job(job_id, product_intel=intel.output)
    if brand is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    casting = await casting_service.run_for_job(
        job_id,
        product_intel=intel.output,
        brand_constraints=brand.output,
    )
    if casting is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    scripts = await script_service.run_for_job(
        job_id,
        product_intel=intel.output,
        brand_constraints=brand.output,
        persona=casting.output,
    )
    if scripts is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    tv_gate_state = job_service.get_tv_gate_state(job_id)
    if tv_gate_state is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if not tv_gate_state["ready_for_render"]:
        return LocalPipelineRunResponse(
            job_id=job_id,
            product_intel_status="cached" if intel.cached else "generated",
            brand_strategy_status="cached" if brand.cached else "generated",
            casting_status="cached" if casting.cached else "generated",
            script_status="cached" if scripts.cached else "generated",
            tv_gate_status=(
                f"blocked_concept_selected_{str(tv_gate_state['concept_selected']).lower()}"
                f"_storyboard_approved_{str(tv_gate_state['storyboard_approved']).lower()}"
            ),
            duration_plan_status="blocked_tv_gates_pending",
            video_generate_status="blocked_tv_gates_pending",
        )

    await duration_planner_service.ensure_units_for_job(job_id)
    units = render_unit_service.list_units(job_id).units
    submitted = 0
    failed = 0
    last_error: str | None = None
    for unit in units:
        for seg in unit.segments:
            if seg.status == "queued":
                try:
                    result = await seedance_pipeline_service.submit_for_segment(
                        job_id=job_id,
                        segment_id=seg.id,
                        idempotency_key=f"local-{job_id}-seg-{seg.id}",
                    )
                except RuntimeError as exc:
                    failed += 1
                    last_error = str(exc)
                    continue

                if str(result.get("status")) == "submitted":
                    submitted += 1
                else:
                    failed += 1

    video_status = f"submitted_{submitted}_failed_{failed}"
    if last_error:
        video_status = f"{video_status}_last_error_{last_error}"
    return LocalPipelineRunResponse(
        job_id=job_id,
        product_intel_status="cached" if intel.cached else "generated",
        brand_strategy_status="cached" if brand.cached else "generated",
        casting_status="cached" if casting.cached else "generated",
        script_status="cached" if scripts.cached else "generated",
        tv_gate_status="ready" if tv_gate_state["required"] else "not_required",
        duration_plan_status="ok",
        video_generate_status=video_status,
    )


@router.get("/{job_id}/tv/gates", response_model=TvGateStatusResponse)
def get_tv_gate_status(job_id: str) -> TvGateStatusResponse:
    try:
        found = job_service.get_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc
    if found is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    state = job_service.get_tv_gate_state(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return TvGateStatusResponse(
        job_id=job_id,
        required=bool(state["required"]),
        concept_selected=bool(state["concept_selected"]),
        selected_concept_id=state["selected_concept_id"],
        storyboard_approved=bool(state["storyboard_approved"]),
        ready_for_render=bool(state["ready_for_render"]),
    )


@router.post("/{job_id}/concepts/select", response_model=TvConceptSelectResponse)
def select_tv_concept(job_id: str, req: TvConceptSelectRequest) -> TvConceptSelectResponse:
    try:
        found = job_service.get_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc
    if found is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if found.mode != "tv":
        raise HTTPException(status_code=400, detail="concept_selection_only_for_tv_mode")

    updated = job_service.select_tv_concept(job_id, req.concept_id.strip())
    if not updated:
        raise HTTPException(status_code=404, detail="job_not_found")
    state = job_service.get_tv_gate_state(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return TvConceptSelectResponse(
        job_id=job_id,
        concept_id=req.concept_id.strip(),
        concept_selected=bool(state["concept_selected"]),
        storyboard_approved=bool(state["storyboard_approved"]),
        ready_for_render=bool(state["ready_for_render"]),
    )


@router.post("/{job_id}/storyboard/approve", response_model=TvStoryboardApproveResponse)
def approve_tv_storyboard(
    job_id: str, req: TvStoryboardApproveRequest
) -> TvStoryboardApproveResponse:
    try:
        found = job_service.get_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc
    if found is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if found.mode != "tv":
        raise HTTPException(status_code=400, detail="storyboard_approval_only_for_tv_mode")

    state = job_service.get_tv_gate_state(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if not state["concept_selected"]:
        raise HTTPException(status_code=400, detail="select_concept_before_storyboard_approval")

    updated = job_service.set_tv_storyboard_approved(job_id, req.approved)
    if not updated:
        raise HTTPException(status_code=404, detail="job_not_found")
    next_state = job_service.get_tv_gate_state(job_id)
    if next_state is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return TvStoryboardApproveResponse(
        job_id=job_id,
        storyboard_approved=bool(next_state["storyboard_approved"]),
        concept_selected=bool(next_state["concept_selected"]),
        ready_for_render=bool(next_state["ready_for_render"]),
    )
