from fastapi import APIRouter, HTTPException
from psycopg import Error as PsycopgError

from app.models.creative import BrandStrategistRunResponse, CastingRunResponse
from app.services.brand_strategy import brand_strategy_service
from app.services.casting import casting_service

router = APIRouter(prefix="/jobs")


@router.post("/{job_id}/brand-strategy", response_model=BrandStrategistRunResponse)
async def run_brand_strategy(job_id: str) -> BrandStrategistRunResponse:
    try:
        result = await brand_strategy_service.run_for_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_operation_failed") from exc
    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result


@router.post("/{job_id}/casting", response_model=CastingRunResponse)
async def run_casting(job_id: str) -> CastingRunResponse:
    try:
        result = await casting_service.run_for_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_operation_failed") from exc
    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result

