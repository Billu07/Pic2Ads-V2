import asyncio
import logging
from typing import Any

import httpx
from psycopg import Error as PsycopgError

from app.clients.kie_client import kie_client
from app.core.config import settings
from app.services.jobs import job_service
from app.services.provider_tasks import provider_task_service
from app.services.render_units import render_unit_service

logger = logging.getLogger(__name__)


def _extract_task_id(kie_response: dict[str, Any]) -> str | None:
    data = kie_response.get("data")
    if isinstance(data, dict):
        task_id = data.get("taskId")
        if isinstance(task_id, str) and task_id:
            return task_id
    return None


class SeedanceRetryWorkerService:
    async def run_once(self, *, batch_size: int | None = None) -> dict[str, int]:
        claimed = provider_task_service.claim_due_retries(
            provider="kie",
            limit=max(1, batch_size or settings.kie_retry_worker_batch_size),
        )

        stats = {
            "claimed": len(claimed),
            "resubmitted": 0,
            "rescheduled": 0,
            "dead_lettered": 0,
        }
        for task in claimed:
            outcome = await self._resubmit_task(task)
            if outcome in stats:
                stats[outcome] += 1
        return stats

    async def run_forever(self, *, poll_interval_seconds: int, batch_size: int) -> None:
        interval = max(1, poll_interval_seconds)
        while True:
            try:
                stats = await self.run_once(batch_size=batch_size)
                if stats["claimed"] > 0:
                    logger.info("seedance retry tick: %s", stats)
            except asyncio.CancelledError:
                raise
            except PsycopgError:
                logger.exception("seedance retry tick failed due to database error")
            except RuntimeError:
                logger.exception("seedance retry tick failed due to configuration/runtime error")
            except Exception:
                logger.exception("seedance retry tick failed unexpectedly")
            await asyncio.sleep(interval)

    async def _resubmit_task(self, task: dict[str, Any]) -> str:
        old_task_id = str(task["provider_task_id"])
        job_id = str(task["job_id"])
        model = task.get("model")
        segment_id = task.get("segment_id")
        retry_count = int(task.get("retry_count") or 0)
        submit_payload = task.get("submit_payload")
        if not isinstance(submit_payload, dict):
            return self._schedule_retry(
                old_task_id=old_task_id,
                job_id=job_id,
                segment_id=segment_id,
                error_message="invalid_retry_submit_payload",
            )

        try:
            kie_response = await kie_client.create_task(submit_payload)
        except RuntimeError as exc:
            return self._schedule_retry(
                old_task_id=old_task_id,
                job_id=job_id,
                segment_id=segment_id,
                error_message=str(exc),
            )
        except httpx.HTTPStatusError as exc:
            return self._schedule_retry(
                old_task_id=old_task_id,
                job_id=job_id,
                segment_id=segment_id,
                error_message=f"kie_http_error_{exc.response.status_code}",
            )
        except httpx.HTTPError:
            return self._schedule_retry(
                old_task_id=old_task_id,
                job_id=job_id,
                segment_id=segment_id,
                error_message="kie_network_error",
            )

        new_task_id = _extract_task_id(kie_response)
        if not new_task_id:
            return self._schedule_retry(
                old_task_id=old_task_id,
                job_id=job_id,
                segment_id=segment_id,
                error_message="kie_task_id_missing",
            )

        try:
            provider_task_service.create_or_update(
                job_id=job_id,
                provider="kie",
                provider_task_id=new_task_id,
                model=str(model) if model else settings.kie_default_model,
                status="submitted",
                submit_payload=submit_payload,
                latest_payload=kie_response,
                segment_id=int(segment_id) if segment_id is not None else None,
                idempotency_key=None,
                submit_hash=None,
                retry_count=retry_count,
            )
            provider_task_service.mark_retried(
                provider="kie",
                provider_task_id=old_task_id,
                replacement_task_id=new_task_id,
            )
            job_service.mark_running(job_id)
            if segment_id is not None:
                render_unit_service.set_segment_status(segment_id=int(segment_id), status="running")
            return "resubmitted"
        except PsycopgError:
            logger.exception("failed to persist seedance retry resubmission for task %s", old_task_id)
            return self._schedule_retry(
                old_task_id=old_task_id,
                job_id=job_id,
                segment_id=segment_id,
                error_message="db_write_failed_for_retry_submit",
            )

    def _schedule_retry(
        self,
        *,
        old_task_id: str,
        job_id: str,
        segment_id: int | None,
        error_message: str,
    ) -> str:
        retry_info = provider_task_service.schedule_retry_or_dead_letter(
            provider="kie",
            provider_task_id=old_task_id,
            error_message=error_message,
            max_retries=settings.kie_max_retries,
            base_delay_seconds=settings.kie_retry_base_delay_seconds,
        )
        if bool(retry_info["dead_lettered"]):
            job_service.set_status(job_id, "failed")
            if segment_id is not None:
                render_unit_service.set_segment_status(segment_id=int(segment_id), status="failed")
            return "dead_lettered"
        return "rescheduled"


seedance_retry_worker_service = SeedanceRetryWorkerService()
