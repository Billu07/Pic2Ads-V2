import hashlib
import json
from typing import Any

import httpx

from app.clients.fal_client import fal_client
from app.core.config import settings
from app.services.jobs import job_service
from app.services.provider_tasks import provider_task_service
from app.services.render_units import render_unit_service


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SeedancePipelineService:
    @staticmethod
    def _extract_request_id(submit_response: dict[str, Any]) -> str | None:
        direct = submit_response.get("request_id")
        if isinstance(direct, str) and direct:
            return direct
        camel = submit_response.get("requestId")
        if isinstance(camel, str) and camel:
            return camel
        return None

    async def submit_for_segment(
        self,
        *,
        job_id: str,
        segment_id: int,
        idempotency_key: str | None = None,
        generate_audio: bool = True,
    ) -> dict[str, Any]:
        context = render_unit_service.get_segment_submission_context(
            job_id=job_id,
            segment_id=segment_id,
        )
        if context is None:
            raise RuntimeError("segment_not_found_for_job")

        product_context = job_service.get_job_product_context(job_id)
        if product_context is None:
            raise RuntimeError("job_not_found")
        product_name, product_image_url = product_context

        prompt = context["prompt_seed"] or f"Handheld product ad shot for {product_name}"
        endpoint_id = settings.fal_seedance_image_endpoint
        arguments: dict[str, Any] = {
            "prompt": prompt,
            "duration": int(context["duration_s"]),
            "aspect_ratio": "9:16",
            "resolution": "720p",
            "generate_audio": bool(generate_audio),
        }
        if context["pattern"] == "extend_chain" and int(context["order"]) > 0:
            previous_segment_id = context["previous_segment_id"]
            previous_output_video_url = context["previous_output_video_url"]
            if previous_segment_id is None:
                return {
                    "job_id": job_id,
                    "segment_id": segment_id,
                    "status": "blocked_extend_previous_missing",
                    "deduped": False,
                }
            if (
                context["previous_segment_status"] != "completed"
                or not isinstance(previous_output_video_url, str)
                or not previous_output_video_url
            ):
                return {
                    "job_id": job_id,
                    "segment_id": segment_id,
                    "status": "blocked_extend_source_pending",
                    "blocked_on_segment_id": previous_segment_id,
                    "deduped": False,
                }
            endpoint_id = settings.fal_seedance_reference_endpoint
            arguments["video_urls"] = [previous_output_video_url]
        else:
            arguments["image_url"] = product_image_url

        submit_payload: dict[str, Any] = {
            "endpoint_id": endpoint_id,
            "arguments": arguments,
            "webhook_url": settings.fal_callback_url,
        }

        submit_hash = _canonical_hash(submit_payload)
        existing = provider_task_service.find_existing_task(
            job_id=job_id,
            provider="fal",
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
            submit_response = await fal_client.submit(
                endpoint_id=endpoint_id,
                arguments=arguments,
                webhook_url=settings.fal_callback_url,
            )
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
        except httpx.HTTPStatusError as exc:
            render_unit_service.set_segment_status(segment_id=segment_id, status="failed")
            status_code = exc.response.status_code if exc.response is not None else 0
            raise RuntimeError(f"fal_submit_http_{status_code}") from exc
        except httpx.HTTPError as exc:
            render_unit_service.set_segment_status(segment_id=segment_id, status="failed")
            raise RuntimeError("fal_submit_network_error") from exc

        task_id = self._extract_request_id(submit_response)
        if not isinstance(task_id, str) or not task_id:
            render_unit_service.set_segment_status(segment_id=segment_id, status="failed")
            raise RuntimeError("fal_request_id_missing")

        provider_task_service.create_or_update(
            job_id=job_id,
            provider="fal",
            provider_task_id=task_id,
            model=endpoint_id,
            status="submitted",
            submit_payload=submit_payload,
            latest_payload=submit_response,
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

    async def auto_continue_extend_chain(
        self,
        *,
        job_id: str,
        completed_segment_id: int,
    ) -> dict[str, Any] | None:
        context = render_unit_service.get_segment_submission_context(
            job_id=job_id,
            segment_id=completed_segment_id,
        )
        if context is None:
            return None
        if context["pattern"] != "extend_chain":
            return None

        next_segment = render_unit_service.get_segment_by_unit_order(
            job_id=job_id,
            render_unit_id=int(context["render_unit_id"]),
            order=int(context["order"]) + 1,
        )
        if next_segment is None:
            return None
        if next_segment.status != "queued":
            return None

        generate_audio = self._infer_generate_audio_from_previous(
            completed_segment_id=completed_segment_id
        )
        return await self.submit_for_segment(
            job_id=job_id,
            segment_id=next_segment.id,
            idempotency_key=f"auto-chain-{job_id}-seg-{next_segment.id}",
            generate_audio=generate_audio,
        )

    @staticmethod
    def _infer_generate_audio_from_previous(*, completed_segment_id: int) -> bool:
        latest = provider_task_service.get_latest_task_for_segment(
            provider="fal",
            segment_id=completed_segment_id,
        )
        if latest is None:
            return True
        submit_payload = latest.get("submit_payload")
        if not isinstance(submit_payload, dict):
            return True
        arguments = submit_payload.get("arguments")
        if not isinstance(arguments, dict):
            return True
        return bool(arguments.get("generate_audio", True))


seedance_pipeline_service = SeedancePipelineService()
