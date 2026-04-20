from dataclasses import dataclass
from datetime import datetime, timezone
import json
from uuid import uuid4

from app.db.client import get_db_connection
from app.models.jobs import CreateJobRequest, JobStatusResponse


@dataclass
class JobRecord:
    id: str
    status: str
    mode: str
    duration_s: int
    created_at: str


class JobService:
    """Postgres-backed job store."""

    def create_job(self, req: CreateJobRequest) -> JobRecord:
        job_id = f"job_{uuid4().hex[:12]}"
        deliverables = [item.model_dump() for item in req.deliverables]

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into public.ad_job (
                      id,
                      brand_id,
                      mode,
                      status,
                      duration_s,
                      product_name,
                      product_image_url,
                      brief,
                      deliverables
                    ) values (%s, %s, %s, 'queued', %s, %s, %s, %s, %s::jsonb)
                    returning id, status::text, mode::text, duration_s, created_at
                    """,
                    (
                        job_id,
                        req.brand_id,
                        req.mode,
                        req.duration_s,
                        req.product.product_name,
                        req.product.product_image_url,
                        req.brief,
                        json.dumps(deliverables),
                    ),
                )
                row = cur.fetchone()
            conn.commit()

        if row is None:
            raise RuntimeError("Failed to create ad_job row.")

        created_at = row["created_at"]
        if isinstance(created_at, datetime):
            created_at_iso = created_at.astimezone(timezone.utc).isoformat()
        else:
            created_at_iso = datetime.now(timezone.utc).isoformat()

        return JobRecord(
            id=str(row["id"]),
            status=str(row["status"]),
            mode=str(row["mode"]),
            duration_s=int(row["duration_s"]),
            created_at=created_at_iso,
        )

    def get_job(self, job_id: str) -> JobStatusResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select id, status::text, mode::text, duration_s, created_at
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()

        if row is None:
            return None

        created_at = row["created_at"]
        if isinstance(created_at, datetime):
            created_at_iso = created_at.astimezone(timezone.utc).isoformat()
        else:
            created_at_iso = datetime.now(timezone.utc).isoformat()

        return JobStatusResponse(
            id=str(row["id"]),
            status=str(row["status"]),
            mode=str(row["mode"]),
            duration_s=int(row["duration_s"]),
            created_at=created_at_iso,
        )

    def get_job_product_context(self, job_id: str) -> tuple[str, str] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select product_name, product_image_url
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return str(row["product_name"]), str(row["product_image_url"])

    def set_status(self, job_id: str, status: str) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.ad_job
                    set status = %s::public.job_status
                    where id = %s
                    """,
                    (status, job_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def mark_running(self, job_id: str) -> bool:
        return self.set_status(job_id, "running")

    def mark_completed(self, job_id: str) -> bool:
        return self.set_status(job_id, "completed")

    def mark_failed(self, job_id: str) -> bool:
        return self.set_status(job_id, "failed")


job_service = JobService()
