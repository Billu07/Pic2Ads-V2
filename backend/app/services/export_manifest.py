from app.db.client import get_db_connection
from app.models.exports import ExportManifestResponse, ExportSegmentItem
from app.services.jobs import job_service


class ExportManifestService:
    def build_manifest(self, *, job_id: str) -> ExportManifestResponse | None:
        if job_service.get_job(job_id) is None:
            return None

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select ru.id as unit_id,
                           ru.sequence as unit_sequence,
                           ru.pattern as unit_pattern,
                           s.id as segment_id,
                           s."order" as segment_order,
                           s.duration_s,
                           s.status,
                           s.prompt_seed,
                           s.output_video_url,
                           s.output_last_frame_url
                    from public.render_unit ru
                    join public.segment s on s.render_unit_id = ru.id
                    where ru.job_id = %s
                    order by ru.sequence asc, s."order" asc
                    """,
                    (job_id,),
                )
                rows = cur.fetchall()

        timeline: list[ExportSegmentItem] = []
        total_duration_s = 0
        ready_duration_s = 0
        units: set[int] = set()

        for row in rows:
            unit_id = int(row["unit_id"])
            duration_s = int(row["duration_s"])
            status = str(row["status"])
            output_video_url = row["output_video_url"]
            ready = status == "completed" and isinstance(output_video_url, str) and bool(output_video_url)

            units.add(unit_id)
            total_duration_s += duration_s
            if ready:
                ready_duration_s += duration_s

            timeline.append(
                ExportSegmentItem(
                    unit_id=unit_id,
                    unit_sequence=int(row["unit_sequence"]),
                    unit_pattern=str(row["unit_pattern"]),
                    segment_id=int(row["segment_id"]),
                    segment_order=int(row["segment_order"]),
                    duration_s=duration_s,
                    status=status,
                    prompt_seed=str(row["prompt_seed"]) if row["prompt_seed"] else None,
                    output_video_url=output_video_url,
                    output_last_frame_url=row["output_last_frame_url"],
                    ready=ready,
                )
            )

        total_segments = len(timeline)
        ready_segments = sum(1 for item in timeline if item.ready)
        missing_segments = total_segments - ready_segments

        if total_segments == 0:
            manifest_status = "empty"
        elif missing_segments == 0:
            manifest_status = "ready"
        else:
            manifest_status = "incomplete"

        return ExportManifestResponse(
            job_id=job_id,
            status=manifest_status,
            total_units=len(units),
            total_segments=total_segments,
            ready_segments=ready_segments,
            missing_segments=missing_segments,
            total_duration_s=total_duration_s,
            ready_duration_s=ready_duration_s,
            timeline=timeline,
        )


export_manifest_service = ExportManifestService()
