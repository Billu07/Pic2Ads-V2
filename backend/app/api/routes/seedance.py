import hashlib
import json
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Query
from psycopg import Error as PsycopgError

from app.clients.fal_client import fal_client
from app.core.config import settings
from app.models.seedance import (
    SeedanceRetryRunResponse,
    SeedanceSubmitRequest,
    SeedanceSubmitResponse,
    SeedanceTaskSyncResponse,
)
from app.services.jobs import job_service
from app.services.provider_payloads import extract_provider_artifacts
from app.services.provider_tasks import provider_task_service
from app.services.render_units import render_unit_service
from app.services.seedance_retry_worker import seedance_retry_worker_service

router = APIRouter(prefix="/jobs")


def _extract_request_id(submit_response: dict[str, Any]) -> str | None:
    direct = submit_response.get("request_id")
    if isinstance(direct, str) and direct:
        return direct
    camel = submit_response.get("requestId")
    if isinstance(camel, str) and camel:
        return camel
    return None


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _extract_queue_status(status_response: dict[str, Any]) -> str | None:
    status = status_response.get("status")
    if isinstance(status, str) and status:
        return status
    return None


def _extract_error_message(status_response: dict[str, Any], result_response: dict[str, Any] | None) -> str | None:
    for source in (status_response, result_response or {}):
        if not isinstance(source, dict):
            continue
        for key in ("error", "message", "detail", "reason"):
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                nested = value.get("message")
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
    return None


def _map_provider_to_job_status(raw_status: str | None, *, has_error: bool) -> str | None:
    if has_error:
        return "failed"
    if not raw_status:
        return None
    normalized = raw_status.strip().upper()
    if normalized in {"IN_QUEUE", "IN_PROGRESS"}:
        return "running"
    if normalized in {"COMPLETED", "OK"}:
        return "completed"
    if normalized in {"ERROR", "FAILED"}:
        return "failed"
    return None


def _is_stale_provider_task_status(status: str | None) -> bool:
    if not status:
        return False
    return status in {"retried", "superseded"}


def _build_fal_arguments(
    *,
    req: SeedanceSubmitRequest,
    product_image_url: str,
) -> tuple[str, dict[str, Any]]:
    base: dict[str, Any] = {
        "prompt": req.prompt,
        "resolution": req.resolution,
        "duration": req.duration,
        "aspect_ratio": req.aspect_ratio,
        "generate_audio": req.generate_audio,
    }
    if req.seed is not None:
        base["seed"] = req.seed
    if req.end_user_id:
        base["end_user_id"] = req.end_user_id

    has_references = bool(
        req.reference_image_urls or req.reference_video_urls or req.reference_audio_urls
    )
    if has_references:
        endpoint = settings.fal_seedance_reference_endpoint
        if req.reference_image_urls:
            base["image_urls"] = req.reference_image_urls
        if req.reference_video_urls:
            base["video_urls"] = req.reference_video_urls
        if req.reference_audio_urls:
            base["audio_urls"] = req.reference_audio_urls
        return endpoint, base

    endpoint = settings.fal_seedance_image_endpoint
    base["image_url"] = req.first_frame_url or product_image_url
    if req.last_frame_url:
        base["end_image_url"] = req.last_frame_url
    return endpoint, base


@router.post("/{job_id}/seedance/submit", response_model=SeedanceSubmitResponse)
async def submit_seedance(
    job_id: str,
    req: SeedanceSubmitRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> SeedanceSubmitResponse:
    try:
        found = job_service.get_job(job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc

    if found is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    try:
        product_context = job_service.get_job_product_context(job_id)
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc

    if product_context is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    _, product_image_url = product_context

    if req.segment_id is not None:
        try:
            belongs = render_unit_service.segment_belongs_to_job(
                segment_id=req.segment_id,
                job_id=job_id,
            )
        except PsycopgError as exc:
            raise HTTPException(status_code=500, detail="db_read_failed") from exc
        if not belongs:
            raise HTTPException(status_code=404, detail="segment_not_found_for_job")

    endpoint_id, arguments = _build_fal_arguments(req=req, product_image_url=product_image_url)
    callback_url = req.callback_url or settings.fal_callback_url
    submit_payload = {
        "endpoint_id": endpoint_id,
        "arguments": arguments,
        "webhook_url": callback_url,
    }
    submit_hash = _canonical_hash(submit_payload)
    try:
        existing = provider_task_service.find_existing_task(
            job_id=job_id,
            provider="fal",
            idempotency_key=idempotency_key,
            submit_hash=submit_hash,
        )
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc

    if existing is not None:
        existing_task_id, existing_status = existing
        return SeedanceSubmitResponse(
            job_id=job_id,
            task_id=existing_task_id,
            provider="fal",
            status=existing_status,
            deduped=True,
        )

    try:
        submit_response = await fal_client.submit(
            endpoint_id=endpoint_id,
            arguments=arguments,
            webhook_url=callback_url,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"fal_http_error_{exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="fal_network_error") from exc

    task_id = _extract_request_id(submit_response)
    if not task_id:
        raise HTTPException(status_code=502, detail="fal_request_id_missing")

    try:
        provider_task_service.create_or_update(
            job_id=job_id,
            provider="fal",
            provider_task_id=task_id,
            model=endpoint_id,
            status="submitted",
            submit_payload=submit_payload,
            latest_payload=submit_response,
            segment_id=req.segment_id,
            idempotency_key=idempotency_key,
            submit_hash=submit_hash,
        )
        job_service.mark_running(job_id)
        if req.segment_id is not None:
            render_unit_service.set_segment_status(segment_id=req.segment_id, status="running")
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_write_failed") from exc

    return SeedanceSubmitResponse(
        job_id=job_id,
        task_id=task_id,
        provider="fal",
        status="submitted",
        deduped=False,
    )


@router.post("/{job_id}/seedance/tasks/{task_id}/sync", response_model=SeedanceTaskSyncResponse)
async def sync_seedance_task(job_id: str, task_id: str) -> SeedanceTaskSyncResponse:
    try:
        mapped = provider_task_service.get_provider_task(provider="fal", provider_task_id=task_id)
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc

    if mapped is None or mapped["job_id"] != job_id:
        raise HTTPException(status_code=404, detail="provider_task_not_found")
    if _is_stale_provider_task_status(mapped.get("status")):
        return SeedanceTaskSyncResponse(
            job_id=job_id,
            task_id=task_id,
            provider="fal",
            provider_status=mapped.get("status"),
            mapped_job_status=None,
            updated=False,
            output_video_url=mapped.get("output_video_url"),
            output_last_frame_url=mapped.get("output_last_frame_url"),
        )

    endpoint_id = str(mapped["model"]) if mapped.get("model") else settings.fal_seedance_image_endpoint
    result_payload: dict[str, Any] | None = None
    try:
        status_payload = await fal_client.status(endpoint_id=endpoint_id, request_id=task_id, with_logs=True)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"fal_http_error_{exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="fal_network_error") from exc

    provider_status = _extract_queue_status(status_payload)
    has_error = bool(status_payload.get("error"))
    mapped_job_status = _map_provider_to_job_status(provider_status, has_error=has_error)
    output_video_url: str | None = None
    output_last_frame_url: str | None = None
    output_metadata: dict[str, Any] = {"status": status_payload}
    error_message = _extract_error_message(status_payload, None)
    updated = False
    retry_count: int | None = None
    next_retry_at: str | None = None
    dead_lettered: bool | None = None

    if provider_status and provider_status.upper() == "COMPLETED" and not has_error:
        try:
            result_payload = await fal_client.result(endpoint_id=endpoint_id, request_id=task_id)
        except httpx.HTTPStatusError as exc:
            has_error = True
            mapped_job_status = "failed"
            error_message = f"fal_result_http_error_{exc.response.status_code}"
        except httpx.HTTPError:
            has_error = True
            mapped_job_status = "failed"
            error_message = "fal_result_network_error"
        if result_payload is not None:
            (
                output_video_url,
                output_last_frame_url,
                extracted_metadata,
                extracted_error,
            ) = extract_provider_artifacts(result_payload)
            output_metadata = {"status": status_payload, "result": extracted_metadata}
            error_message = extracted_error or error_message
            mapped_job_status = "failed" if error_message else "completed"

    try:
        if provider_status:
            provider_task_service.update_from_webhook(
                provider="fal",
                provider_task_id=task_id,
                status=provider_status,
                latest_payload={"status": status_payload, "result": result_payload or {}},
                output_video_url=output_video_url,
                output_last_frame_url=output_last_frame_url,
                output_metadata=output_metadata,
                error_message=error_message if mapped_job_status == "failed" else None,
                completed_at_now=mapped_job_status == "completed",
            )
        effective_job_status = mapped_job_status
        if mapped_job_status == "failed":
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

        if effective_job_status:
            updated = job_service.set_status(job_id, effective_job_status)
        if mapped.get("segment_id") is not None and mapped_job_status:
            segment_status = mapped_job_status
            if mapped_job_status == "failed":
                segment_status = "failed" if (dead_lettered is True) else "running"
            render_unit_service.set_segment_status(
                segment_id=int(mapped["segment_id"]),
                status=segment_status,
            )
            render_unit_service.set_segment_outputs(
                segment_id=int(mapped["segment_id"]),
                output_video_url=output_video_url,
                output_last_frame_url=output_last_frame_url,
            )
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_write_failed") from exc

    return SeedanceTaskSyncResponse(
        job_id=job_id,
        task_id=task_id,
        provider="fal",
        provider_status=provider_status,
        mapped_job_status=mapped_job_status,
        updated=updated,
        output_video_url=output_video_url,
        output_last_frame_url=output_last_frame_url,
        retry_count=retry_count,
        next_retry_at=next_retry_at,
        dead_lettered=dead_lettered,
    )


@router.post("/seedance/retries/run", response_model=SeedanceRetryRunResponse)
async def run_seedance_retries(
    batch_size: int | None = Query(default=None, ge=1, le=100),
) -> SeedanceRetryRunResponse:
    try:
        stats = await seedance_retry_worker_service.run_once(batch_size=batch_size)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_write_failed") from exc

    return SeedanceRetryRunResponse(
        provider="fal",
        claimed=int(stats["claimed"]),
        resubmitted=int(stats["resubmitted"]),
        rescheduled=int(stats["rescheduled"]),
        dead_lettered=int(stats["dead_lettered"]),
    )
