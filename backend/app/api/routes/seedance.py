import hashlib
import json
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Query
from psycopg import Error as PsycopgError

from app.clients.kie_client import kie_client
from app.core.config import settings
from app.models.seedance import (
    SeedanceRetryRunResponse,
    SeedanceSubmitRequest,
    SeedanceSubmitResponse,
    SeedanceTaskSyncResponse,
)
from app.services.jobs import job_service
from app.services.provider_payloads import extract_provider_artifacts
from app.services.seedance_retry_worker import seedance_retry_worker_service
from app.services.provider_tasks import provider_task_service
from app.services.render_units import render_unit_service

router = APIRouter(prefix="/jobs")


def _extract_task_id(kie_response: dict[str, Any]) -> str | None:
    data = kie_response.get("data")
    if isinstance(data, dict):
        task_id = data.get("taskId")
        if isinstance(task_id, str) and task_id:
            return task_id
    return None


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _extract_detail_status(detail_response: dict[str, Any]) -> str | None:
    status = detail_response.get("status")
    if isinstance(status, str) and status:
        return status
    data = detail_response.get("data")
    if isinstance(data, dict):
        s = data.get("status")
        if isinstance(s, str) and s:
            return s
    return None


def _map_provider_to_job_status(raw_status: str | None, code: int | None = None) -> str | None:
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


def _is_stale_provider_task_status(status: str | None) -> bool:
    if not status:
        return False
    return status in {"retried", "superseded"}


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

    callback_url = req.callback_url or settings.kie_callback_url
    input_payload: dict[str, Any] = {
        "prompt": req.prompt,
        "duration": req.duration,
        "aspect_ratio": req.aspect_ratio,
        "resolution": req.resolution,
        "generate_audio": req.generate_audio,
        "web_search": req.web_search,
        "nsfw_checker": req.nsfw_checker,
    }

    # Default to the job image as first frame if no other image/video references were supplied.
    if req.first_frame_url:
        input_payload["first_frame_url"] = req.first_frame_url
    elif not (req.reference_image_urls or req.reference_video_urls or req.reference_audio_urls):
        input_payload["first_frame_url"] = product_image_url

    if req.last_frame_url:
        input_payload["last_frame_url"] = req.last_frame_url
    if req.reference_image_urls:
        input_payload["reference_image_urls"] = req.reference_image_urls
    if req.reference_video_urls:
        input_payload["reference_video_urls"] = req.reference_video_urls
    if req.reference_audio_urls:
        input_payload["reference_audio_urls"] = req.reference_audio_urls

    body: dict[str, Any] = {
        "model": settings.kie_default_model,
        "input": input_payload,
    }
    if callback_url:
        body["callBackUrl"] = callback_url

    submit_hash = _canonical_hash(body)
    try:
        existing = provider_task_service.find_existing_task(
            job_id=job_id,
            provider="kie",
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
            provider="kie",
            status=existing_status,
            deduped=True,
        )

    try:
        kie_response = await kie_client.create_task(body)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"kie_http_error_{exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="kie_network_error") from exc

    task_id = _extract_task_id(kie_response)
    if not task_id:
        raise HTTPException(status_code=502, detail="kie_task_id_missing")

    try:
        provider_task_service.create_or_update(
            job_id=job_id,
            provider="kie",
            provider_task_id=task_id,
            model=settings.kie_default_model,
            status="submitted",
            submit_payload=body,
            latest_payload=kie_response,
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
        provider="kie",
        status="submitted",
        deduped=False,
    )


@router.post("/{job_id}/seedance/tasks/{task_id}/sync", response_model=SeedanceTaskSyncResponse)
async def sync_seedance_task(job_id: str, task_id: str) -> SeedanceTaskSyncResponse:
    try:
        mapped = provider_task_service.get_provider_task(provider="kie", provider_task_id=task_id)
    except PsycopgError as exc:
        raise HTTPException(status_code=500, detail="db_read_failed") from exc

    if mapped is None or mapped["job_id"] != job_id:
        raise HTTPException(status_code=404, detail="provider_task_not_found")
    if _is_stale_provider_task_status(mapped.get("status")):
        return SeedanceTaskSyncResponse(
            job_id=job_id,
            task_id=task_id,
            provider="kie",
            provider_status=mapped.get("status"),
            mapped_job_status=None,
            updated=False,
            output_video_url=mapped.get("output_video_url"),
            output_last_frame_url=mapped.get("output_last_frame_url"),
        )

    try:
        detail = await kie_client.get_task_detail(task_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"kie_http_error_{exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="kie_network_error") from exc

    provider_status = _extract_detail_status(detail)
    mapped_job_status = _map_provider_to_job_status(provider_status, detail.get("code"))
    output_video_url, output_last_frame_url, output_metadata, error_message = extract_provider_artifacts(
        detail
    )
    updated = False
    retry_count: int | None = None
    next_retry_at: str | None = None
    dead_lettered: bool | None = None

    try:
        if provider_status:
            provider_task_service.update_from_webhook(
                provider="kie",
                provider_task_id=task_id,
                status=provider_status,
                latest_payload=detail,
                output_video_url=output_video_url,
                output_last_frame_url=output_last_frame_url,
                output_metadata=output_metadata,
                error_message=error_message if mapped_job_status == "failed" else None,
                completed_at_now=mapped_job_status == "completed",
            )
        effective_job_status = mapped_job_status
        if mapped_job_status == "failed":
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
        provider="kie",
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
        provider="kie",
        claimed=int(stats["claimed"]),
        resubmitted=int(stats["resubmitted"]),
        rescheduled=int(stats["rescheduled"]),
        dead_lettered=int(stats["dead_lettered"]),
    )
