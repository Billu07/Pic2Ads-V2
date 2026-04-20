from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from psycopg import Error as PsycopgError

from app.core.config import settings
from app.models.webhooks import KieWebhookPayload, KieWebhookResponse
from app.services.jobs import job_service
from app.services.provider_payloads import extract_provider_artifacts
from app.services.provider_tasks import provider_task_service
from app.services.render_units import render_unit_service

router = APIRouter(prefix="/webhooks")


def _is_stale_provider_task_status(status: str | None) -> bool:
    if not status:
        return False
    return status in {"retried", "superseded"}


def _extract_job_id(payload: KieWebhookPayload, query_job_id: str | None) -> str | None:
    if query_job_id:
        return query_job_id
    if payload.job_id:
        return payload.job_id
    if payload.data and isinstance(payload.data, dict):
        direct = payload.data.get("job_id")
        if isinstance(direct, str) and direct:
            return direct
        metadata = payload.data.get("metadata")
        if isinstance(metadata, dict):
            meta_job = metadata.get("job_id")
            if isinstance(meta_job, str) and meta_job:
                return meta_job
    return None


def _extract_task_id(payload: KieWebhookPayload) -> str | None:
    if payload.taskId:
        return payload.taskId
    if payload.data and isinstance(payload.data, dict):
        direct = payload.data.get("taskId")
        if isinstance(direct, str) and direct:
            return direct
    return None


def _map_status(raw_status: str | None, code: int | None) -> str | None:
    if raw_status:
        normalized = raw_status.strip().lower()
        if normalized in {"success", "completed", "succeeded", "done"}:
            return "completed"
        if normalized in {"failed", "error", "cancelled"}:
            return "failed"
        if normalized in {"running", "processing", "queued", "in_progress"}:
            return "running"
    if code == 200:
        return "completed"
    if code and code >= 400:
        return "failed"
    return None


@router.post("/kie", response_model=KieWebhookResponse)
def kie_callback(
    payload: KieWebhookPayload,
    job_id: str | None = Query(default=None),
    x_kie_webhook_secret: str | None = Header(default=None),
) -> KieWebhookResponse:
    expected_secret = settings.kie_webhook_secret
    if expected_secret and x_kie_webhook_secret != expected_secret:
        raise HTTPException(status_code=401, detail="invalid_webhook_secret")

    task_id = _extract_task_id(payload)
    resolved_job_id = _extract_job_id(payload, job_id)
    provider_task_record: dict[str, Any] | None = None

    if task_id:
        try:
            provider_task_record = provider_task_service.get_provider_task(
                provider="kie",
                provider_task_id=task_id,
            )
        except PsycopgError as exc:
            raise HTTPException(status_code=500, detail="db_lookup_failed") from exc
        if provider_task_record and not resolved_job_id:
            resolved_job_id = str(provider_task_record["job_id"])

    mapped_status = _map_status(payload.status, payload.code)
    provider_task_status = payload.status or mapped_status
    output_video_url, output_last_frame_url, output_metadata, error_message = extract_provider_artifacts(
        payload.model_dump()
    )
    completed_now = bool(mapped_status == "completed")
    failed_now = bool(mapped_status == "failed")
    retry_count: int | None = None
    next_retry_at: str | None = None
    dead_lettered: bool | None = None

    if provider_task_record and _is_stale_provider_task_status(provider_task_record.get("status")):
        return KieWebhookResponse(
            accepted=True,
            job_id=resolved_job_id,
            mapped_status=mapped_status,
            updated=False,
            output_video_url=output_video_url,
            output_last_frame_url=output_last_frame_url,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            dead_lettered=dead_lettered,
        )

    if task_id and provider_task_status:
        try:
            provider_task_service.update_from_webhook(
                provider="kie",
                provider_task_id=task_id,
                status=provider_task_status,
                latest_payload=payload.model_dump(),
                output_video_url=output_video_url,
                output_last_frame_url=output_last_frame_url,
                output_metadata=output_metadata,
                error_message=error_message if failed_now else None,
                completed_at_now=completed_now,
            )
        except PsycopgError as exc:
            raise HTTPException(status_code=500, detail="db_provider_task_update_failed") from exc

    if not resolved_job_id or not mapped_status:
        return KieWebhookResponse(
            accepted=True,
            job_id=resolved_job_id,
            mapped_status=mapped_status,
            updated=False,
            output_video_url=output_video_url,
            output_last_frame_url=output_last_frame_url,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            dead_lettered=dead_lettered,
        )

    try:
        effective_job_status = mapped_status
        if mapped_status == "failed" and task_id:
            retry_info = provider_task_service.schedule_retry_or_dead_letter(
                provider="kie",
                provider_task_id=task_id,
                error_message=error_message,
                max_retries=settings.kie_max_retries,
                base_delay_seconds=settings.kie_retry_base_delay_seconds,
            )
            retry_count = int(retry_info["retry_count"])
            next_retry_at = retry_info["next_retry_at"]
            dead_lettered = bool(retry_info["dead_lettered"])
            effective_job_status = "failed" if dead_lettered else "running"

        updated = job_service.set_status(resolved_job_id, effective_job_status)
        if provider_task_record and provider_task_record.get("segment_id") is not None:
            segment_id = int(provider_task_record["segment_id"])
            segment_status = mapped_status
            if mapped_status == "failed":
                segment_status = "failed" if (dead_lettered is True) else "running"
            render_unit_service.set_segment_status(segment_id=segment_id, status=segment_status)
            render_unit_service.set_segment_outputs(
                segment_id=segment_id,
                output_video_url=output_video_url,
                output_last_frame_url=output_last_frame_url,
            )
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_status_update_failed") from exc

    return KieWebhookResponse(
        accepted=True,
        job_id=resolved_job_id,
        mapped_status=mapped_status,
        updated=updated,
        output_video_url=output_video_url,
        output_last_frame_url=output_last_frame_url,
        retry_count=retry_count,
        next_retry_at=next_retry_at,
        dead_lettered=dead_lettered,
    )
