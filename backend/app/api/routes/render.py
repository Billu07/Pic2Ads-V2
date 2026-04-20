from fastapi import APIRouter, HTTPException
from psycopg import Error as PsycopgError

from app.models.render import (
    RenderUnitCreateRequest,
    RenderUnitListResponse,
    RenderUnitResponse,
    SegmentRegenRequest,
    SegmentRegenResponse,
)
from app.services.render_units import render_unit_service

router = APIRouter(prefix="/jobs")


@router.post("/{job_id}/units", response_model=RenderUnitResponse)
def create_render_unit(job_id: str, req: RenderUnitCreateRequest) -> RenderUnitResponse:
    try:
        created = render_unit_service.create_unit(job_id, req)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_write_failed") from exc

    if created is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return created


@router.get("/{job_id}/units", response_model=RenderUnitListResponse)
def list_render_units(job_id: str) -> RenderUnitListResponse:
    try:
        return render_unit_service.list_units(job_id)
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc


@router.post("/{job_id}/segments/{segment_id}/regen", response_model=SegmentRegenResponse)
def regen_segment(job_id: str, segment_id: int, req: SegmentRegenRequest) -> SegmentRegenResponse:
    try:
        updated = render_unit_service.regen_segment(job_id=job_id, segment_id=segment_id, req=req)
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_write_failed") from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="segment_not_found_for_job")
    return updated
