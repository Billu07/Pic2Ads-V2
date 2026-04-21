from app.db.client import get_db_connection
from app.models.render import (
    SegmentRegenRequest,
    SegmentRegenResponse,
    RenderUnitCreateRequest,
    RenderUnitListResponse,
    RenderUnitResponse,
    SegmentResponse,
)


class RenderUnitService:
    def get_segment_submission_context(self, *, job_id: str, segment_id: int) -> dict | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                      s.id,
                      s.render_unit_id,
                      s."order",
                      s.duration_s,
                      s.prompt_seed,
                      s.status,
                      s.output_video_url,
                      s.output_last_frame_url,
                      ru.pattern,
                      prev.id as previous_segment_id,
                      prev.status as previous_segment_status,
                      prev.output_video_url as previous_output_video_url
                    from public.segment s
                    join public.render_unit ru on ru.id = s.render_unit_id
                    left join public.segment prev
                      on prev.render_unit_id = s.render_unit_id
                     and prev."order" = s."order" - 1
                    where ru.job_id = %s
                      and s.id = %s
                    """,
                    (job_id, segment_id),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "segment_id": int(row["id"]),
            "render_unit_id": int(row["render_unit_id"]),
            "order": int(row["order"]),
            "duration_s": int(row["duration_s"]),
            "prompt_seed": str(row["prompt_seed"]) if row["prompt_seed"] else None,
            "status": str(row["status"]),
            "output_video_url": row["output_video_url"],
            "output_last_frame_url": row["output_last_frame_url"],
            "pattern": str(row["pattern"]),
            "previous_segment_id": (
                int(row["previous_segment_id"]) if row["previous_segment_id"] is not None else None
            ),
            "previous_segment_status": (
                str(row["previous_segment_status"]) if row["previous_segment_status"] else None
            ),
            "previous_output_video_url": row["previous_output_video_url"],
        }

    def get_segment_by_unit_order(
        self,
        *,
        job_id: str,
        render_unit_id: int,
        order: int,
    ) -> SegmentResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select s.id, s."order", s.duration_s, s.prompt_seed, s.status, s.output_video_url, s.output_last_frame_url
                    from public.segment s
                    join public.render_unit ru on ru.id = s.render_unit_id
                    where ru.job_id = %s
                      and s.render_unit_id = %s
                      and s."order" = %s
                    """,
                    (job_id, render_unit_id, order),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return SegmentResponse(
            id=int(row["id"]),
            order=int(row["order"]),
            duration_s=int(row["duration_s"]),
            prompt_seed=str(row["prompt_seed"]) if row["prompt_seed"] else None,
            status=str(row["status"]),
            output_video_url=row["output_video_url"],
            output_last_frame_url=row["output_last_frame_url"],
        )

    def create_unit(self, job_id: str, req: RenderUnitCreateRequest) -> RenderUnitResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select 1 from public.ad_job where id = %s", (job_id,))
                if cur.fetchone() is None:
                    return None

                cur.execute(
                    """
                    insert into public.render_unit (job_id, sequence, pattern, duration_s)
                    values (%s, %s, %s, %s)
                    returning id, sequence, pattern, duration_s
                    """,
                    (job_id, req.sequence, req.pattern, req.duration_s),
                )
                unit_row = cur.fetchone()
                if unit_row is None:
                    raise RuntimeError("Failed to create render_unit row.")

                unit_id = int(unit_row["id"])
                segments: list[SegmentResponse] = []
                for seg in req.segments:
                    cur.execute(
                        """
                        insert into public.segment (render_unit_id, "order", duration_s, prompt_seed, status)
                        values (%s, %s, %s, %s, 'queued')
                        returning id, "order", duration_s, prompt_seed, status, output_video_url, output_last_frame_url
                        """,
                        (unit_id, seg.order, seg.duration_s, seg.prompt_seed),
                    )
                    seg_row = cur.fetchone()
                    if seg_row is None:
                        raise RuntimeError("Failed to create segment row.")
                    segments.append(
                        SegmentResponse(
                            id=int(seg_row["id"]),
                            order=int(seg_row["order"]),
                            duration_s=int(seg_row["duration_s"]),
                            prompt_seed=str(seg_row["prompt_seed"]) if seg_row["prompt_seed"] else None,
                            status=str(seg_row["status"]),
                            output_video_url=seg_row["output_video_url"],
                            output_last_frame_url=seg_row["output_last_frame_url"],
                        )
                    )
            conn.commit()

        return RenderUnitResponse(
            id=int(unit_row["id"]),
            sequence=int(unit_row["sequence"]),
            pattern=str(unit_row["pattern"]),
            duration_s=int(unit_row["duration_s"]),
            segments=segments,
        )

    def list_units(self, job_id: str) -> RenderUnitListResponse:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select id, sequence, pattern, duration_s
                    from public.render_unit
                    where job_id = %s
                    order by sequence asc
                    """,
                    (job_id,),
                )
                units_rows = cur.fetchall()

                unit_ids = [int(r["id"]) for r in units_rows]
                segments_by_unit: dict[int, list[SegmentResponse]] = {uid: [] for uid in unit_ids}
                if unit_ids:
                    cur.execute(
                        """
                        select id, render_unit_id, "order", duration_s, prompt_seed, status, output_video_url, output_last_frame_url
                        from public.segment
                        where render_unit_id = any(%s)
                        order by render_unit_id asc, "order" asc
                        """,
                        (unit_ids,),
                    )
                    for row in cur.fetchall():
                        uid = int(row["render_unit_id"])
                        segments_by_unit[uid].append(
                            SegmentResponse(
                                id=int(row["id"]),
                                order=int(row["order"]),
                                duration_s=int(row["duration_s"]),
                                prompt_seed=str(row["prompt_seed"]) if row["prompt_seed"] else None,
                                status=str(row["status"]),
                                output_video_url=row["output_video_url"],
                                output_last_frame_url=row["output_last_frame_url"],
                            )
                        )

        units = [
            RenderUnitResponse(
                id=int(r["id"]),
                sequence=int(r["sequence"]),
                pattern=str(r["pattern"]),
                duration_s=int(r["duration_s"]),
                segments=segments_by_unit.get(int(r["id"]), []),
            )
            for r in units_rows
        ]
        return RenderUnitListResponse(job_id=job_id, units=units)

    def segment_belongs_to_job(self, *, segment_id: int, job_id: str) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select 1
                    from public.segment s
                    join public.render_unit ru on ru.id = s.render_unit_id
                    where s.id = %s and ru.job_id = %s
                    """,
                    (segment_id, job_id),
                )
                return cur.fetchone() is not None

    def set_segment_status(self, *, segment_id: int, status: str) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.segment
                    set status = %s
                    where id = %s
                    """,
                    (status, segment_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def set_segment_outputs(
        self,
        *,
        segment_id: int,
        output_video_url: str | None,
        output_last_frame_url: str | None,
    ) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.segment
                    set output_video_url = coalesce(%s, output_video_url),
                        output_last_frame_url = coalesce(%s, output_last_frame_url)
                    where id = %s
                    """,
                    (output_video_url, output_last_frame_url, segment_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def get_segment_for_job(self, *, job_id: str, segment_id: int) -> SegmentResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select s.id, s."order", s.duration_s, s.prompt_seed, s.status, s.output_video_url, s.output_last_frame_url
                    from public.segment s
                    join public.render_unit ru on ru.id = s.render_unit_id
                    where ru.job_id = %s and s.id = %s
                    """,
                    (job_id, segment_id),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return SegmentResponse(
            id=int(row["id"]),
            order=int(row["order"]),
            duration_s=int(row["duration_s"]),
            prompt_seed=str(row["prompt_seed"]) if row["prompt_seed"] else None,
            status=str(row["status"]),
            output_video_url=row["output_video_url"],
            output_last_frame_url=row["output_last_frame_url"],
        )

    def regen_segment(
        self,
        *,
        job_id: str,
        segment_id: int,
        req: SegmentRegenRequest,
    ) -> SegmentRegenResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select s.id
                    from public.segment s
                    join public.render_unit ru on ru.id = s.render_unit_id
                    where ru.job_id = %s and s.id = %s
                    """,
                    (job_id, segment_id),
                )
                if cur.fetchone() is None:
                    return None

                if req.clear_outputs:
                    cur.execute(
                        """
                        update public.segment
                        set status = 'queued',
                            prompt_seed = coalesce(%s, prompt_seed),
                            output_video_url = null,
                            output_last_frame_url = null
                        where id = %s
                        returning id, "order", duration_s, prompt_seed, status, output_video_url, output_last_frame_url
                        """,
                        (req.prompt_seed, segment_id),
                    )
                else:
                    cur.execute(
                        """
                        update public.segment
                        set status = 'queued',
                            prompt_seed = coalesce(%s, prompt_seed)
                        where id = %s
                        returning id, "order", duration_s, prompt_seed, status, output_video_url, output_last_frame_url
                        """,
                        (req.prompt_seed, segment_id),
                    )
                row = cur.fetchone()

                cur.execute(
                    """
                    update public.provider_task
                    set status = 'superseded'
                    where segment_id = %s
                      and status not in ('completed', 'failed', 'dead_lettered')
                    """,
                    (segment_id,),
                )

            conn.commit()

        if row is None:
            return None

        segment = SegmentResponse(
            id=int(row["id"]),
            order=int(row["order"]),
            duration_s=int(row["duration_s"]),
            prompt_seed=str(row["prompt_seed"]) if row["prompt_seed"] else None,
            status=str(row["status"]),
            output_video_url=row["output_video_url"],
            output_last_frame_url=row["output_last_frame_url"],
        )
        return SegmentRegenResponse(job_id=job_id, segment=segment)


render_unit_service = RenderUnitService()
