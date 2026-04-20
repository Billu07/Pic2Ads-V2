from fastapi import APIRouter, HTTPException
from psycopg import Error as PsycopgError

from app.models.product_intel import ProductIntelRunResponse
from app.services.product_intel import product_intel_service

router = APIRouter(prefix="/jobs")


@router.post("/{job_id}/intel", response_model=ProductIntelRunResponse)
async def run_product_intel(job_id: str) -> ProductIntelRunResponse:
    try:
        result = await product_intel_service.run_for_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_operation_failed") from exc

    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result

