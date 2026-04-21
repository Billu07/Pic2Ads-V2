from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from psycopg import Error as PsycopgError

from app.core.config import settings
from app.models.webhooks import FalWebhookPayload, FalWebhookResponse
from app.services.jobs import job_service
from app.services.provider_payloads import extract_provider_artifacts
from app.services.provider_tasks import provider_task_service
from app.services.render_units import render_unit_service
from app.services.seedance_pipeline import seedance_pipeline_service

router = APIRouter(prefix="/webhooks")


def _is_stale_provider_task_status(status: str | None) -> bool:
    if not status:
        return False
    return status in {"retried", "superseded"}


def _extract_job_id(payload: FalWebhookPayload, query_job_id: str | None) -> str | None:
    if query_job_id:
        return query_job_id
    if payload.job_id:
        return payload.job_id
    if payload.payload and isinstance(payload.payload, dict):
        metadata = payload.payload.get("metadata")
        if isinstance(metadata, dict):
            meta_job = metadata.get("job_id")
            if isinstance(meta_job, str) and meta_job:
                return meta_job
    if payload.data and isinstance(payload.data, dict):
        direct = payload.data.get("job_id")
        if isinstance(direct, str) and direct:
            return direct
    return None


def _extract_task_id(payload: FalWebhookPayload) -> str | None:
    if payload.request_id:
        return payload.request_id
    if payload.taskId:
        return payload.taskId
    if payload.data and isinstance(payload.data, dict):
        direct = payload.data.get("taskId")
        if isinstance(direct, str) and direct:
            return direct
    return None


def _extract_error_text(payload: FalWebhookPayload) -> str | None:
    if isinstance(payload.error, str) and payload.error.strip():
        return payload.error.strip()
    if isinstance(payload.error, dict):
        message = payload.error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    if payload.payload and isinstance(payload.payload, dict):
        error = payload.payload.get("error")
        if isinstance(error, str) and error.strip():
            return error.strip()
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
    return None


def _map_status(raw_status: str | None, has_error: bool) -> str | None:
    if has_error:
        return "failed"
    if raw_status:
        normalized = raw_status.strip().upper()
        if normalized in {"OK", "COMPLETED"}:
            return "completed"
        if normalized in {"ERROR", "FAILED"}:
            return "failed"
        if normalized in {"IN_QUEUE", "IN_PROGRESS"}:
            return "running"
    return None


async def _handle_fal_callback(
    *,
    payload: FalWebhookPayload,
    job_id: str | None,
    provided_secret: str | None,
) -> FalWebhookResponse:
    expected_secret = settings.fal_webhook_secret
    if expected_secret and provided_secret != expected_secret:
        raise HTTPException(status_code=401, detail="invalid_webhook_secret")

    task_id = _extract_task_id(payload)
    resolved_job_id = _extract_job_id(payload, job_id)
    provider_task_record: dict[str, Any] | None = None

    if task_id:
        try:
            provider_task_record = provider_task_service.get_provider_task(
                provider="fal",
                provider_task_id=task_id,
            )
        except PsycopgError as exc:
            raise HTTPException(status_code=500, detail="db_lookup_failed") from exc
        if provider_task_record and not resolved_job_id:
            resolved_job_id = str(provider_task_record["job_id"])

    has_error = bool(payload.error)
    mapped_status = _map_status(payload.status, has_error=has_error)
    provider_task_status = payload.status or mapped_status
    output_video_url, output_last_frame_url, output_metadata, artifact_error = extract_provider_artifacts(
        payload.payload if isinstance(payload.payload, dict) else payload.model_dump()
    )
    error_message = artifact_error or _extract_error_text(payload)
    completed_now = bool(mapped_status == "completed")
    failed_now = bool(mapped_status == "failed")
    retry_count: int | None = None
    next_retry_at: str | None = None
    dead_lettered: bool | None = None

    if provider_task_record and _is_stale_provider_task_status(provider_task_record.get("status")):
        return FalWebhookResponse(
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
                provider="fal",
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
        return FalWebhookResponse(
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
                provider="fal",
                provider_task_id=task_id,
                error_message=error_message,
                max_retries=settings.fal_max_retries,
                base_delay_seconds=settings.fal_retry_base_delay_seconds,
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

    if (
        mapped_status == "completed"
        and resolved_job_id
        and provider_task_record
        and provider_task_record.get("segment_id") is not None
    ):
        try:
            await seedance_pipeline_service.auto_continue_extend_chain(
                job_id=resolved_job_id,
                completed_segment_id=int(provider_task_record["segment_id"]),
            )
        except RuntimeError:
            # Do not fail webhook acknowledgement on continuation attempt.
            pass

    return FalWebhookResponse(
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


@router.post("/fal", response_model=FalWebhookResponse)
async def fal_callback(
    payload: FalWebhookPayload,
    job_id: str | None = Query(default=None),
    secret: str | None = Query(default=None),
    x_fal_webhook_secret: str | None = Header(default=None),
) -> FalWebhookResponse:
    return await _handle_fal_callback(
        payload=payload,
        job_id=job_id,
        provided_secret=x_fal_webhook_secret or secret,
    )


@router.post("/kie", response_model=FalWebhookResponse)
async def legacy_kie_callback_alias(
    payload: FalWebhookPayload,
    job_id: str | None = Query(default=None),
    secret: str | None = Query(default=None),
    x_fal_webhook_secret: str | None = Header(default=None),
) -> FalWebhookResponse:
    # Temporary alias to avoid breaking existing callback URLs during provider transition.
    return await _handle_fal_callback(
        payload=payload,
        job_id=job_id,
        provided_secret=x_fal_webhook_secret or secret,
    )
