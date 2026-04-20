import hashlib
import json
from typing import Any

import httpx

from app.clients.kie_client import kie_client
from app.core.config import settings
from app.services.jobs import job_service
from app.services.provider_tasks import provider_task_service
from app.services.render_units import render_unit_service


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SeedancePipelineService:
    async def submit_for_segment(
        self,
        *,
        job_id: str,
        segment_id: int,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        segment = render_unit_service.get_segment_for_job(job_id=job_id, segment_id=segment_id)
        if segment is None:
            raise RuntimeError("segment_not_found_for_job")

        product_context = job_service.get_job_product_context(job_id)
        if product_context is None:
            raise RuntimeError("job_not_found")
        product_name, product_image_url = product_context

        prompt = segment.prompt_seed or f"Handheld product ad shot for {product_name}"
        input_payload: dict[str, Any] = {
            "prompt": prompt,
            "duration": segment.duration_s,
            "aspect_ratio": "9:16",
            "resolution": "720p",
            "generate_audio": False,
            "web_search": False,
            "nsfw_checker": False,
            "first_frame_url": product_image_url,
        }

        body: dict[str, Any] = {
            "model": settings.kie_default_model,
            "input": input_payload,
        }
        if settings.kie_callback_url:
            body["callBackUrl"] = settings.kie_callback_url

        submit_hash = _canonical_hash(body)
        existing = provider_task_service.find_existing_task(
            job_id=job_id,
            provider="kie",
            idempotency_key=idempotency_key,
            submit_hash=submit_hash,
        )
        if existing is not None:
            task_id, status = existing
            return {
                "job_id": job_id,
                "segment_id": segment_id,
                "task_id": task_id,
                "status": status,
                "deduped": True,
            }

        try:
            kie_response = await kie_client.create_task(body)
        except RuntimeError:
            # Credentials missing: keep segment queued/running flow non-fatal in development.
            render_unit_service.set_segment_status(segment_id=segment_id, status="queued")
            return {
                "job_id": job_id,
                "segment_id": segment_id,
                "task_id": None,
                "status": "queued",
                "deduped": False,
            }
        except (httpx.HTTPError, httpx.HTTPStatusError) as exc:
            render_unit_service.set_segment_status(segment_id=segment_id, status="failed")
            raise RuntimeError("kie_submit_failed") from exc

        api_code = kie_response.get("code")
        api_msg = kie_response.get("msg")
        if isinstance(api_code, int) and api_code != 200:
            render_unit_service.set_segment_status(segment_id=segment_id, status="failed")
            detail = f"kie_api_error_code_{api_code}"
            if isinstance(api_msg, str) and api_msg.strip():
                detail = f"{detail}:{api_msg.strip()}"
            raise RuntimeError(detail)

        data = kie_response.get("data")
        task_id = data.get("taskId") if isinstance(data, dict) else None
        if not isinstance(task_id, str) or not task_id:
            render_unit_service.set_segment_status(segment_id=segment_id, status="failed")
            detail = "kie_task_id_missing"
            if isinstance(api_msg, str) and api_msg.strip():
                detail = f"{detail}:{api_msg.strip()}"
            raise RuntimeError(detail)

        provider_task_service.create_or_update(
            job_id=job_id,
            provider="kie",
            provider_task_id=task_id,
            model=settings.kie_default_model,
            status="submitted",
            submit_payload=body,
            latest_payload=kie_response,
            segment_id=segment_id,
            idempotency_key=idempotency_key,
            submit_hash=submit_hash,
        )
        job_service.mark_running(job_id)
        render_unit_service.set_segment_status(segment_id=segment_id, status="running")

        return {
            "job_id": job_id,
            "segment_id": segment_id,
            "task_id": task_id,
            "status": "submitted",
            "deduped": False,
        }


seedance_pipeline_service = SeedancePipelineService()
