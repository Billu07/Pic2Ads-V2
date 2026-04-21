import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.client import get_db_connection


class ProviderTaskService:
    def create_or_update(
        self,
        *,
        job_id: str,
        provider: str,
        provider_task_id: str,
        model: str | None,
        status: str,
        submit_payload: dict[str, Any],
        latest_payload: dict[str, Any],
        segment_id: int | None = None,
        idempotency_key: str | None = None,
        submit_hash: str | None = None,
        output_video_url: str | None = None,
        output_last_frame_url: str | None = None,
        output_metadata: dict[str, Any] | None = None,
        error_message: str | None = None,
        completed_at_now: bool = False,
        retry_count: int | None = None,
    ) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into public.provider_task (
                      job_id, provider, provider_task_id, model, status, submit_payload, latest_payload,
                      segment_id, idempotency_key, submit_hash, output_video_url, output_last_frame_url,
                      output_metadata, error_message, completed_at, retry_count
                    ) values (
                      %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s::jsonb, %s,
                      case when %s then timezone('utc', now()) else null end,
                      coalesce(%s, 0)
                    )
                    on conflict (provider, provider_task_id)
                    do update set
                      status = excluded.status,
                      model = excluded.model,
                      latest_payload = excluded.latest_payload,
                      segment_id = coalesce(excluded.segment_id, public.provider_task.segment_id),
                      idempotency_key = coalesce(excluded.idempotency_key, public.provider_task.idempotency_key),
                      submit_hash = coalesce(excluded.submit_hash, public.provider_task.submit_hash),
                      output_video_url = coalesce(excluded.output_video_url, public.provider_task.output_video_url),
                      output_last_frame_url = coalesce(excluded.output_last_frame_url, public.provider_task.output_last_frame_url),
                      output_metadata = public.provider_task.output_metadata || excluded.output_metadata,
                      error_message = coalesce(excluded.error_message, public.provider_task.error_message),
                      completed_at = coalesce(public.provider_task.completed_at, excluded.completed_at),
                      retry_count = case
                        when %s then excluded.retry_count
                        else public.provider_task.retry_count
                      end
                    """,
                    (
                        job_id,
                        provider,
                        provider_task_id,
                        model,
                        status,
                        json.dumps(submit_payload),
                        json.dumps(latest_payload),
                        segment_id,
                        idempotency_key,
                        submit_hash,
                        output_video_url,
                        output_last_frame_url,
                        json.dumps(output_metadata or {}),
                        error_message,
                        completed_at_now,
                        retry_count,
                        retry_count is not None,
                    ),
                )
            conn.commit()

    def claim_due_retries(self, *, provider: str, limit: int) -> list[dict[str, Any]]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    with due as (
                      select id
                      from public.provider_task
                      where provider = %s
                        and status = 'retry_scheduled'
                        and dead_lettered = false
                        and next_retry_at is not null
                        and next_retry_at <= timezone('utc', now())
                      order by next_retry_at asc, id asc
                      limit %s
                      for update skip locked
                    )
                    update public.provider_task p
                    set status = 'retrying',
                        next_retry_at = null
                    from due
                    where p.id = due.id
                    returning p.job_id, p.provider_task_id, p.model, p.submit_payload, p.segment_id, p.retry_count
                    """,
                    (provider, limit),
                )
                rows = cur.fetchall()
            conn.commit()

        claimed: list[dict[str, Any]] = []
        for row in rows:
            claimed.append(
                {
                    "job_id": str(row["job_id"]),
                    "provider_task_id": str(row["provider_task_id"]),
                    "model": str(row["model"]) if row["model"] else None,
                    "submit_payload": row["submit_payload"],
                    "segment_id": int(row["segment_id"]) if row["segment_id"] is not None else None,
                    "retry_count": int(row["retry_count"] or 0),
                }
            )
        return claimed

    def find_existing_task(
        self,
        *,
        job_id: str,
        provider: str,
        idempotency_key: str | None,
        submit_hash: str | None,
    ) -> tuple[str, str] | None:
        clauses: list[str] = []
        params: list[str] = [job_id, provider]

        if idempotency_key:
            clauses.append("idempotency_key = %s")
            params.append(idempotency_key)
        if submit_hash:
            clauses.append("submit_hash = %s")
            params.append(submit_hash)

        if not clauses:
            return None

        condition = " or ".join(clauses)
        query = f"""
            select provider_task_id, status
            from public.provider_task
            where job_id = %s
              and provider = %s
              and ({condition})
            order by created_at desc
            limit 1
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                row = cur.fetchone()
        if row is None:
            return None
        return str(row["provider_task_id"]), str(row["status"])

    def get_job_id_by_provider_task(self, *, provider: str, provider_task_id: str) -> str | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select job_id
                    from public.provider_task
                    where provider = %s and provider_task_id = %s
                    """,
                    (provider, provider_task_id),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return str(row["job_id"])

    def get_provider_task(
        self,
        *,
        provider: str,
        provider_task_id: str,
    ) -> dict[str, Any] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select job_id, provider_task_id, status, model, latest_payload
                         , segment_id, output_video_url, output_last_frame_url, output_metadata,
                           error_message, completed_at, retry_count, next_retry_at, last_error_at, dead_lettered
                    from public.provider_task
                    where provider = %s and provider_task_id = %s
                    """,
                    (provider, provider_task_id),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "job_id": str(row["job_id"]),
            "provider_task_id": str(row["provider_task_id"]),
            "status": str(row["status"]),
            "model": str(row["model"]) if row["model"] else None,
            "latest_payload": row["latest_payload"],
            "segment_id": int(row["segment_id"]) if row["segment_id"] is not None else None,
            "output_video_url": row["output_video_url"],
            "output_last_frame_url": row["output_last_frame_url"],
            "output_metadata": row["output_metadata"],
            "error_message": row["error_message"],
            "completed_at": row["completed_at"],
            "retry_count": int(row["retry_count"]) if row["retry_count"] is not None else 0,
            "next_retry_at": row["next_retry_at"],
            "last_error_at": row["last_error_at"],
            "dead_lettered": bool(row["dead_lettered"]) if row["dead_lettered"] is not None else False,
        }

    def get_latest_task_for_segment(
        self,
        *,
        provider: str,
        segment_id: int,
    ) -> dict[str, Any] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select provider_task_id, status, submit_payload, latest_payload, model, job_id
                    from public.provider_task
                    where provider = %s
                      and segment_id = %s
                    order by created_at desc
                    limit 1
                    """,
                    (provider, segment_id),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "provider_task_id": str(row["provider_task_id"]),
            "status": str(row["status"]),
            "submit_payload": row["submit_payload"] if isinstance(row["submit_payload"], dict) else {},
            "latest_payload": row["latest_payload"] if isinstance(row["latest_payload"], dict) else {},
            "model": str(row["model"]) if row["model"] else None,
            "job_id": str(row["job_id"]),
        }

    def update_from_webhook(
        self,
        *,
        provider: str,
        provider_task_id: str,
        status: str,
        latest_payload: dict[str, Any],
        output_video_url: str | None = None,
        output_last_frame_url: str | None = None,
        output_metadata: dict[str, Any] | None = None,
        error_message: str | None = None,
        completed_at_now: bool = False,
    ) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.provider_task
                    set status = %s,
                        latest_payload = %s::jsonb,
                        output_video_url = coalesce(%s, output_video_url),
                        output_last_frame_url = coalesce(%s, output_last_frame_url),
                        output_metadata = output_metadata || %s::jsonb,
                        error_message = coalesce(%s, error_message),
                        completed_at = case when %s then coalesce(completed_at, timezone('utc', now())) else completed_at end
                    where provider = %s and provider_task_id = %s
                    """,
                    (
                        status,
                        json.dumps(latest_payload),
                        output_video_url,
                        output_last_frame_url,
                        json.dumps(output_metadata or {}),
                        error_message,
                        completed_at_now,
                        provider,
                        provider_task_id,
                    ),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def schedule_retry_or_dead_letter(
        self,
        *,
        provider: str,
        provider_task_id: str,
        error_message: str | None,
        max_retries: int,
        base_delay_seconds: int,
    ) -> dict[str, Any]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select retry_count, dead_lettered
                    from public.provider_task
                    where provider = %s and provider_task_id = %s
                    """,
                    (provider, provider_task_id),
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError("provider_task_not_found")

                current_retry = int(row["retry_count"] or 0)
                next_retry_count = current_retry + 1
                now = datetime.now(timezone.utc)

                if next_retry_count > max_retries:
                    cur.execute(
                        """
                        update public.provider_task
                        set dead_lettered = true,
                            status = 'dead_lettered',
                            retry_count = %s,
                            next_retry_at = null,
                            last_error_at = %s,
                            error_message = coalesce(%s, error_message)
                        where provider = %s and provider_task_id = %s
                        returning retry_count, next_retry_at, dead_lettered
                        """,
                        (next_retry_count, now, error_message, provider, provider_task_id),
                    )
                else:
                    delay = base_delay_seconds * (2 ** (next_retry_count - 1))
                    next_retry_at = now + timedelta(seconds=delay)
                    cur.execute(
                        """
                        update public.provider_task
                        set dead_lettered = false,
                            status = 'retry_scheduled',
                            retry_count = %s,
                            next_retry_at = %s,
                            last_error_at = %s,
                            error_message = coalesce(%s, error_message)
                        where provider = %s and provider_task_id = %s
                        returning retry_count, next_retry_at, dead_lettered
                        """,
                        (next_retry_count, next_retry_at, now, error_message, provider, provider_task_id),
                    )

                updated = cur.fetchone()
            conn.commit()

        if updated is None:
            raise RuntimeError("provider_task_update_failed")

        next_retry = updated["next_retry_at"]
        return {
            "retry_count": int(updated["retry_count"]),
            "next_retry_at": next_retry.isoformat() if isinstance(next_retry, datetime) else None,
            "dead_lettered": bool(updated["dead_lettered"]),
        }

    def mark_retried(
        self,
        *,
        provider: str,
        provider_task_id: str,
        replacement_task_id: str,
    ) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.provider_task
                    set status = 'retried',
                        next_retry_at = null,
                        latest_payload = latest_payload || %s::jsonb
                    where provider = %s and provider_task_id = %s
                    """,
                    (
                        json.dumps({"retry_replaced_by_task_id": replacement_task_id}),
                        provider,
                        provider_task_id,
                    ),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated


provider_task_service = ProviderTaskService()
