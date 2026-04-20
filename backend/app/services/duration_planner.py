from app.models.render import RenderUnitCreateRequest, SegmentCreateRequest
from app.services.jobs import job_service
from app.services.render_units import render_unit_service


class DurationPlannerService:
    def ensure_units_for_job(self, job_id: str) -> int:
        existing = render_unit_service.list_units(job_id).units
        if existing:
            return len(existing)

        job = job_service.get_job(job_id)
        if job is None:
            raise RuntimeError("job_not_found")

        total = int(job.duration_s)
        segments: list[SegmentCreateRequest] = []
        remaining = total
        order = 0
        while remaining > 0:
            seg_dur = min(15, remaining)
            segments.append(
                SegmentCreateRequest(
                    order=order,
                    duration_s=seg_dur,
                    prompt_seed=f"Segment {order + 1} render seed for job {job_id}",
                )
            )
            order += 1
            remaining -= seg_dur

        pattern = "single_gen" if len(segments) == 1 else "extend_chain"
        req = RenderUnitCreateRequest(
            sequence=0,
            pattern=pattern,
            duration_s=total,
            segments=segments,
        )
        created = render_unit_service.create_unit(job_id, req)
        if created is None:
            raise RuntimeError("job_not_found")
        return 1


duration_planner_service = DurationPlannerService()

