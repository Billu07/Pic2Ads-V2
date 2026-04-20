from fastapi import APIRouter, HTTPException
from psycopg import Error as PsycopgError

from app.models.scripts import ScriptRunResponse
from app.services.scripts import script_service

router = APIRouter(prefix="/jobs")


@router.post("/{job_id}/scripts", response_model=ScriptRunResponse)
async def run_screenwriter(job_id: str) -> ScriptRunResponse:
    try:
        result = await script_service.run_for_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_operation_failed") from exc

    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result

