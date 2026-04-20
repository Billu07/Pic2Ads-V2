from fastapi import APIRouter, HTTPException
from psycopg import Error as PsycopgError

from app.models.exports import ExportManifestResponse
from app.services.export_manifest import export_manifest_service

router = APIRouter(prefix="/jobs")


@router.get("/{job_id}/export/manifest", response_model=ExportManifestResponse)
def get_export_manifest(job_id: str) -> ExportManifestResponse:
    try:
        manifest = export_manifest_service.build_manifest(job_id=job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc

    if manifest is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return manifest
