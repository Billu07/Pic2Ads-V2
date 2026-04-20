from temporalio import activity

from app.services.duration_planner import duration_planner_service
from app.services.product_intel import product_intel_service
from app.services.render_units import render_unit_service
from app.services.seedance_pipeline import seedance_pipeline_service


@activity.defn
async def product_intel_activity(job_id: str) -> dict[str, str]:
    result = await product_intel_service.run_for_job(job_id)
    if result is None:
        return {"job_id": job_id, "activity": "product_intel", "status": "job_not_found"}
    return {
        "job_id": job_id,
        "activity": "product_intel",
        "status": "completed",
        "cached": "true" if result.cached else "false",
    }


@activity.defn
async def duration_plan_activity(job_id: str) -> dict[str, str]:
    count = duration_planner_service.ensure_units_for_job(job_id)
    return {"job_id": job_id, "activity": "duration_plan", "status": "completed", "units": str(count)}


@activity.defn
async def video_generate_activity(job_id: str) -> dict[str, str]:
    units = render_unit_service.list_units(job_id).units
    submitted = 0
    for unit in units:
        for seg in unit.segments:
            if seg.status == "queued":
                await seedance_pipeline_service.submit_for_segment(
                    job_id=job_id,
                    segment_id=seg.id,
                    idempotency_key=f"wf-{job_id}-seg-{seg.id}",
                )
                submitted += 1
    return {
        "job_id": job_id,
        "activity": "video_generate",
        "status": "completed",
        "submitted_segments": str(submitted),
    }
