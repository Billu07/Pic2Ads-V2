from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any
from uuid import uuid4

from app.db.client import get_db_connection
from app.models.jobs import CreateJobRequest, JobStatusResponse
from app.models.prompting import CreativeDecisions, CreativeDecisionsInput


@dataclass
class JobRecord:
    id: str
    status: str
    mode: str
    duration_s: int
    created_at: str


class JobService:
    """Postgres-backed job store."""
    _LANGUAGE_MAP: dict[str, str] = {
        "en": "English",
        "bn": "Bengali",
        "hi": "Hindi",
        "es": "Spanish",
    }

    @staticmethod
    def _default_creative_decisions(mode: str) -> CreativeDecisions:
        if mode == "pro_arc":
            return CreativeDecisions(
                tone="cinematic but grounded",
                hook_style="storytime_confession",
                offer_angle="emotional_relief",
                cta_style="question_prompt",
                must_include=["one grounded personal moment", "visible product use beat"],
                must_avoid=["over-polished ad language"],
            )
        if mode == "tv":
            return CreativeDecisions(
                tone="premium narrative clarity",
                hook_style="problem_first",
                offer_angle="performance_proof",
                cta_style="direct_command",
                must_include=["clear problem-to-relief progression", "hero product beat"],
                must_avoid=["low-trust clickbait phrasing"],
            )
        return CreativeDecisions(
            tone="raw and relatable",
            hook_style="demo_first",
            offer_angle="speed_convenience",
            cta_style="soft_invite",
            must_include=["natural handheld cadence"],
            must_avoid=["scripted corporate wording"],
        )

    @staticmethod
    def _prompt_pack_id_for_mode(mode: str) -> str:
        return {
            "ugc": "ugc_core_v1",
            "pro_arc": "pro_arc_arc_v1",
            "tv": "tv_campaign_v1",
        }.get(mode, "ugc_core_v1")

    @classmethod
    def _merge_creative_decisions(
        cls, mode: str, updates: CreativeDecisionsInput | None
    ) -> CreativeDecisions:
        defaults = cls._default_creative_decisions(mode)
        if updates is None:
            return defaults
        raw = updates.model_dump(exclude_none=True)
        return defaults.model_copy(update=raw)

    @classmethod
    def _default_workflow_state(
        cls,
        mode: str,
        creative_updates: CreativeDecisionsInput | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        language_code = language if language in cls._LANGUAGE_MAP else "en"
        state: dict[str, Any] = {
            "language": language_code,
            "creative": {
                "mode": mode,
                "prompt_pack_id": cls._prompt_pack_id_for_mode(mode),
                "decisions": cls._merge_creative_decisions(mode, creative_updates).model_dump(),
            }
        }
        if mode == "tv":
            state["tv"] = {
                "concept_selected": False,
                "selected_concept_id": None,
                "storyboard_concept_id": None,
                "storyboard": [],
                "storyboard_approved": False,
                "concepts": [],
            }
        return state

    @staticmethod
    def _extract_tv_state(workflow_state: dict[str, Any]) -> dict[str, Any]:
        tv_state = workflow_state.get("tv", {})
        if not isinstance(tv_state, dict):
            return {}
        return tv_state

    def create_job(self, req: CreateJobRequest) -> JobRecord:
        job_id = f"job_{uuid4().hex[:12]}"
        deliverables = [item.model_dump() for item in req.deliverables]
        workflow_state = self._default_workflow_state(
            req.mode,
            req.creative_decisions,
            language=req.language,
        )

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
                      deliverables,
                      workflow_state
                    ) values (%s, %s, %s, 'queued', %s, %s, %s, %s, %s::jsonb, %s::jsonb)
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
                        json.dumps(workflow_state),
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

    def list_jobs(self, *, limit: int, offset: int) -> tuple[list[JobStatusResponse], int]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select count(*) as total from public.ad_job")
                total_row = cur.fetchone()
                total = int(total_row["total"]) if total_row else 0

                cur.execute(
                    """
                    select id, status::text, mode::text, duration_s, created_at
                    from public.ad_job
                    order by created_at desc
                    limit %s
                    offset %s
                    """,
                    (limit, offset),
                )
                rows = cur.fetchall()

        items: list[JobStatusResponse] = []
        for row in rows:
            created_at = row["created_at"]
            if isinstance(created_at, datetime):
                created_at_iso = created_at.astimezone(timezone.utc).isoformat()
            else:
                created_at_iso = datetime.now(timezone.utc).isoformat()
            items.append(
                JobStatusResponse(
                    id=str(row["id"]),
                    status=str(row["status"]),
                    mode=str(row["mode"]),
                    duration_s=int(row["duration_s"]),
                    created_at=created_at_iso,
                )
            )
        return items, total

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

    def get_workflow_state(self, job_id: str) -> dict[str, Any] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select workflow_state
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        state = row["workflow_state"]
        return state if isinstance(state, dict) else {}

    def get_creative_context(self, job_id: str) -> dict[str, Any] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select mode::text as mode, workflow_state
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None

        mode = str(row["mode"])
        state = row["workflow_state"] if isinstance(row["workflow_state"], dict) else {}
        creative = state.get("creative", {}) if isinstance(state, dict) else {}
        creative_decisions_raw = (
            creative.get("decisions", {}) if isinstance(creative, dict) else {}
        )
        updates = (
            CreativeDecisionsInput.model_validate(creative_decisions_raw)
            if isinstance(creative_decisions_raw, dict)
            else None
        )
        decisions = self._merge_creative_decisions(mode, updates)

        prompt_pack_id = self._prompt_pack_id_for_mode(mode)
        if isinstance(creative, dict) and isinstance(creative.get("prompt_pack_id"), str):
            prompt_pack_id = str(creative["prompt_pack_id"])
        language_code = "en"
        if isinstance(state.get("language"), str) and state["language"] in self._LANGUAGE_MAP:
            language_code = str(state["language"])

        return {
            "job_id": job_id,
            "mode": mode,
            "prompt_pack_id": prompt_pack_id,
            "language_code": language_code,
            "language_name": self._LANGUAGE_MAP.get(language_code, "English"),
            "decisions": decisions.model_dump(),
        }

    def set_creative_decisions(
        self, job_id: str, updates: CreativeDecisionsInput
    ) -> dict[str, Any] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select mode::text as mode from public.ad_job where id = %s", (job_id,))
                row = cur.fetchone()
                if row is None:
                    return None
                mode = str(row["mode"])
                decisions = self._merge_creative_decisions(mode, updates)
                creative_payload = {
                    "mode": mode,
                    "prompt_pack_id": self._prompt_pack_id_for_mode(mode),
                    "decisions": decisions.model_dump(),
                }
                cur.execute(
                    """
                    update public.ad_job
                    set workflow_state = jsonb_set(
                      coalesce(workflow_state, '{}'::jsonb),
                      '{creative}',
                      %s::jsonb,
                      true
                    )
                    where id = %s
                    """,
                    (json.dumps(creative_payload), job_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        if not updated:
            return None
        return {
            "job_id": job_id,
            "mode": mode,
            "prompt_pack_id": str(creative_payload["prompt_pack_id"]),
            "decisions": decisions.model_dump(),
        }

    def get_tv_gate_state(self, job_id: str) -> dict[str, Any] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select mode::text as mode, workflow_state
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        if str(row["mode"]) != "tv":
            return {
                "mode": str(row["mode"]),
                "concept_selected": True,
                "selected_concept_id": None,
                "storyboard_generated": True,
                "storyboard_approved": True,
                "ready_for_render": True,
                "required": False,
            }
        state = row["workflow_state"] if isinstance(row["workflow_state"], dict) else {}
        tv_state = self._extract_tv_state(state)
        concept_selected = bool(tv_state.get("concept_selected", False))
        storyboard_approved = bool(tv_state.get("storyboard_approved", False))
        selected_concept_id = tv_state.get("selected_concept_id")
        if not isinstance(selected_concept_id, str):
            selected_concept_id = None
        storyboard_concept_id = tv_state.get("storyboard_concept_id")
        if not isinstance(storyboard_concept_id, str):
            storyboard_concept_id = None
        storyboard = tv_state.get("storyboard")
        storyboard_generated = (
            isinstance(storyboard, list)
            and len(storyboard) > 0
            and selected_concept_id is not None
            and storyboard_concept_id == selected_concept_id
        )
        return {
            "mode": "tv",
            "concept_selected": concept_selected,
            "selected_concept_id": selected_concept_id,
            "storyboard_generated": storyboard_generated,
            "storyboard_approved": storyboard_approved,
            "ready_for_render": concept_selected and storyboard_generated and storyboard_approved,
            "required": True,
        }

    def get_tv_concepts(self, job_id: str) -> list[dict[str, Any]] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select mode::text as mode, workflow_state
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        if str(row["mode"]) != "tv":
            return []
        state = row["workflow_state"] if isinstance(row["workflow_state"], dict) else {}
        tv_state = self._extract_tv_state(state)
        concepts = tv_state.get("concepts")
        if not isinstance(concepts, list):
            return []
        out: list[dict[str, Any]] = []
        for item in concepts:
            if isinstance(item, dict):
                out.append(item)
        return out

    def set_tv_concepts(self, job_id: str, concepts: list[dict[str, Any]]) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.ad_job
                    set workflow_state = jsonb_set(
                      jsonb_set(
                        jsonb_set(
                          jsonb_set(
                            jsonb_set(
                              jsonb_set(coalesce(workflow_state, '{}'::jsonb),
                                        '{tv,concepts}', %s::jsonb, true),
                              '{tv,concept_selected}', 'false'::jsonb, true
                            ),
                            '{tv,storyboard}', '[]'::jsonb, true
                          ),
                          '{tv,storyboard_concept_id}', 'null'::jsonb, true
                        ),
                        '{tv,storyboard_approved}', 'false'::jsonb, true
                      ),
                      '{tv,selected_concept_id}', 'null'::jsonb, true
                    )
                    where id = %s
                      and mode = 'tv'
                    """,
                    (json.dumps(concepts), job_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def select_tv_concept(self, job_id: str, concept_id: str) -> tuple[bool, str | None]:
        concepts = self.get_tv_concepts(job_id)
        if concepts is None:
            return False, "job_not_found"
        allowed_ids = {
            str(item.get("concept_id"))
            for item in concepts
            if isinstance(item.get("concept_id"), str)
        }
        if concept_id not in allowed_ids:
            return False, "concept_id_not_generated"

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.ad_job
                    set workflow_state = jsonb_set(
                      jsonb_set(
                        jsonb_set(
                          jsonb_set(
                            jsonb_set(coalesce(workflow_state, '{}'::jsonb),
                                      '{tv,selected_concept_id}', to_jsonb(%s::text), true),
                            '{tv,concept_selected}', 'true'::jsonb, true
                          ),
                          '{tv,storyboard}', '[]'::jsonb, true
                        ),
                        '{tv,storyboard_concept_id}', 'null'::jsonb, true
                      ),
                      '{tv,storyboard_approved}', 'false'::jsonb, true
                    )
                    where id = %s
                      and mode = 'tv'
                    """,
                    (concept_id, job_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        if not updated:
            return False, "job_not_found"
        return True, None

    def get_tv_storyboard(self, job_id: str) -> dict[str, Any] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select mode::text as mode, workflow_state
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        if str(row["mode"]) != "tv":
            return {"concept_id": None, "shots": []}
        state = row["workflow_state"] if isinstance(row["workflow_state"], dict) else {}
        tv_state = self._extract_tv_state(state)
        concept_id = tv_state.get("storyboard_concept_id")
        if not isinstance(concept_id, str):
            concept_id = None
        shots = tv_state.get("storyboard")
        if not isinstance(shots, list):
            shots = []
        return {"concept_id": concept_id, "shots": [s for s in shots if isinstance(s, dict)]}

    def set_tv_storyboard(self, job_id: str, *, concept_id: str, shots: list[dict[str, Any]]) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.ad_job
                    set workflow_state = jsonb_set(
                      jsonb_set(
                        jsonb_set(
                          coalesce(workflow_state, '{}'::jsonb),
                          '{tv,storyboard}', %s::jsonb, true
                        ),
                        '{tv,storyboard_concept_id}', to_jsonb(%s::text), true
                      ),
                      '{tv,storyboard_approved}', 'false'::jsonb, true
                    )
                    where id = %s
                      and mode = 'tv'
                    """,
                    (json.dumps(shots), concept_id, job_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def set_tv_storyboard_approved(self, job_id: str, approved: bool) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.ad_job
                    set workflow_state = jsonb_set(
                      coalesce(workflow_state, '{}'::jsonb),
                      '{tv,storyboard_approved}',
                      to_jsonb(%s::boolean),
                      true
                    )
                    where id = %s
                      and mode = 'tv'
                    """,
                    (approved, job_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def get_language_code(self, job_id: str) -> str:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select workflow_state
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return "en"
        workflow_state = row["workflow_state"] if isinstance(row["workflow_state"], dict) else {}
        language = workflow_state.get("language")
        if isinstance(language, str) and language in self._LANGUAGE_MAP:
            return language
        return "en"

    def set_render_selection(
        self,
        job_id: str,
        *,
        selected_variant_id: str | None,
        selected_variant_sequence: int | None,
        render_all_variants: bool,
    ) -> bool:
        payload = {
            "selected_variant_id": selected_variant_id,
            "selected_variant_sequence": selected_variant_sequence,
            "render_all_variants": bool(render_all_variants),
        }
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update public.ad_job
                    set workflow_state = jsonb_set(
                      coalesce(workflow_state, '{}'::jsonb),
                      '{render}',
                      %s::jsonb,
                      true
                    )
                    where id = %s
                    """,
                    (json.dumps(payload), job_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
        return updated

    def get_render_selection(self, job_id: str) -> dict[str, Any] | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select workflow_state
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None

        workflow_state = row["workflow_state"] if isinstance(row["workflow_state"], dict) else {}
        render = workflow_state.get("render")
        if not isinstance(render, dict):
            return {}
        out: dict[str, Any] = {}
        if isinstance(render.get("selected_variant_id"), str):
            out["selected_variant_id"] = render["selected_variant_id"]
        if isinstance(render.get("selected_variant_sequence"), int):
            out["selected_variant_sequence"] = int(render["selected_variant_sequence"])
        if isinstance(render.get("render_all_variants"), bool):
            out["render_all_variants"] = bool(render["render_all_variants"])
        return out

    def mark_running(self, job_id: str) -> bool:
        return self.set_status(job_id, "running")

    def mark_completed(self, job_id: str) -> bool:
        return self.set_status(job_id, "completed")

    def mark_failed(self, job_id: str) -> bool:
        return self.set_status(job_id, "failed")


job_service = JobService()
