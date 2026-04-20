import json

import httpx

from app.clients.openai_client import openai_client
from app.models.concepts import TvConcept
from app.models.storyboard import (
    TvStoryboardGenerateInput,
    TvStoryboardGenerateOutput,
    TvStoryboardGenerateResponse,
    TvStoryboardListResponse,
    TvStoryboardShot,
)
from app.services.brand_strategy import brand_strategy_service
from app.services.casting import casting_service
from app.services.jobs import job_service
from app.services.prompt_orchestration import prompt_orchestration_service
from app.services.product_intel import product_intel_service


class StoryboardService:
    async def generate_for_job(self, job_id: str) -> TvStoryboardGenerateResponse | None:
        gate = job_service.get_tv_gate_state(job_id)
        if gate is None:
            return None
        if not gate["required"]:
            raise RuntimeError("storyboard_generation_only_for_tv_mode")
        if not gate["concept_selected"] or not gate["selected_concept_id"]:
            raise RuntimeError("select_concept_before_storyboard_generation")
        selected_concept_id = str(gate["selected_concept_id"])

        existing = job_service.get_tv_storyboard(job_id)
        if existing is None:
            return None
        if (
            existing.get("concept_id") == selected_concept_id
            and isinstance(existing.get("shots"), list)
            and len(existing["shots"]) > 0
        ):
            shots = [TvStoryboardShot.model_validate(item) for item in existing["shots"]]
            return TvStoryboardGenerateResponse(
                job_id=job_id,
                concept_id=selected_concept_id,
                cached=True,
                shots=shots,
            )

        concepts = job_service.get_tv_concepts(job_id)
        if concepts is None:
            return None
        selected_raw = next(
            (
                item
                for item in concepts
                if isinstance(item.get("concept_id"), str) and item["concept_id"] == selected_concept_id
            ),
            None,
        )
        if selected_raw is None:
            raise RuntimeError("concept_id_not_generated")
        selected_concept = TvConcept.model_validate(selected_raw)

        job = job_service.get_job(job_id)
        if job is None:
            return None
        product_context = job_service.get_job_product_context(job_id)
        if product_context is None:
            return None
        product_name, _ = product_context

        intel_run = await product_intel_service.run_for_job(job_id)
        if intel_run is None:
            return None
        brand_run = await brand_strategy_service.run_for_job(job_id, product_intel=intel_run.output)
        if brand_run is None:
            return None
        casting_run = await casting_service.run_for_job(
            job_id,
            product_intel=intel_run.output,
            brand_constraints=brand_run.output,
        )
        if casting_run is None:
            return None

        prompt_context = prompt_orchestration_service.get_for_job(job_id)
        if prompt_context is None:
            return None

        payload = TvStoryboardGenerateInput(
            product_name=product_name,
            brief=self._read_job_brief(job_id),
            duration_s=job.duration_s,
            prompt_pack_id=str(prompt_context["prompt_pack_id"]),
            prompt_directives=list(prompt_context["storyboard_directives"]),
            creative_decisions=prompt_context["creative_decisions"],
            selected_concept=selected_concept,
            product_intel=intel_run.output,
            brand_constraints=brand_run.output,
            persona=casting_run.output,
        )
        try:
            generated = await openai_client.tv_storyboard_from_context(payload)
            normalized = self._normalize_generated(generated, target_duration_s=job.duration_s)
        except (RuntimeError, httpx.HTTPError, ValueError, json.JSONDecodeError):
            normalized = self._heuristic_fallback(payload)

        dumped = [shot.model_dump() for shot in normalized.shots]
        saved = job_service.set_tv_storyboard(
            job_id, concept_id=selected_concept_id, shots=dumped
        )
        if not saved:
            return None
        return TvStoryboardGenerateResponse(
            job_id=job_id,
            concept_id=selected_concept_id,
            cached=False,
            shots=normalized.shots,
        )

    def list_for_job(self, job_id: str) -> TvStoryboardListResponse | None:
        data = job_service.get_tv_storyboard(job_id)
        if data is None:
            return None
        concept_id = data.get("concept_id")
        if not isinstance(concept_id, str):
            concept_id = None
        raw_shots = data.get("shots")
        if not isinstance(raw_shots, list):
            raw_shots = []
        shots = [TvStoryboardShot.model_validate(item) for item in raw_shots if isinstance(item, dict)]
        return TvStoryboardListResponse(
            job_id=job_id,
            concept_id=concept_id,
            generated=bool(shots),
            shots=shots,
        )

    @staticmethod
    def _read_job_brief(job_id: str) -> str | None:
        from app.db.client import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select brief from public.ad_job where id = %s", (job_id,))
                row = cur.fetchone()
        if row is None or row["brief"] is None:
            return None
        return str(row["brief"])

    def _normalize_generated(
        self, output: TvStoryboardGenerateOutput, *, target_duration_s: int
    ) -> TvStoryboardGenerateOutput:
        shots = output.shots[:8]
        if len(shots) < 3:
            return self._heuristic_fallback_from_existing(shots, target_duration_s=target_duration_s)

        normalized: list[TvStoryboardShot] = []
        for idx, shot in enumerate(shots):
            transition = shot.transition_in
            if idx == 0:
                transition = "opening"
            elif transition == "opening":
                transition = "hard_cut"
            normalized.append(
                shot.model_copy(
                    update={
                        "shot_id": f"shot_{idx + 1}",
                        "sequence": idx,
                        "transition_in": transition,
                    }
                )
            )
        durations = [shot.duration_s for shot in normalized]
        balanced = self._rebalance_duration(durations, target_duration_s=target_duration_s)
        normalized = [
            shot.model_copy(update={"duration_s": balanced[idx]})
            for idx, shot in enumerate(normalized)
        ]
        return TvStoryboardGenerateOutput(shots=normalized)

    def _heuristic_fallback(self, payload: TvStoryboardGenerateInput) -> TvStoryboardGenerateOutput:
        parts = self._rebalance_duration([8, 7, 8, 7], target_duration_s=payload.duration_s)
        shots = [
            TvStoryboardShot(
                shot_id=f"shot_{idx + 1}",
                sequence=idx,
                duration_s=parts[idx],
                purpose=purpose,
                visual_description=visual,
                camera_intent=camera,
                transition_in="opening" if idx == 0 else "hard_cut",
            )
            for idx, (purpose, visual, camera) in enumerate(
                [
                    (
                        "Establish problem context",
                        f"Introduce persona in real setting with {payload.product_name} nearby.",
                        "handheld_follow",
                    ),
                    (
                        "Introduce product in-use",
                        f"Show practical use of {payload.product_name} tied to the main pain point.",
                        "slow_push_in",
                    ),
                    (
                        "Demonstrate core feature",
                        "Focus on one concrete interaction beat proving usefulness.",
                        "close_up_reaction",
                    ),
                    (
                        "Resolve with confidence",
                        "End on composed hero frame with authentic emotional release.",
                        "slow_pull_out",
                    ),
                ]
            )
        ]
        return TvStoryboardGenerateOutput(shots=shots)

    def _heuristic_fallback_from_existing(
        self, existing: list[TvStoryboardShot], *, target_duration_s: int
    ) -> TvStoryboardGenerateOutput:
        if not existing:
            parts = self._rebalance_duration([8, 7, 8, 7], target_duration_s=target_duration_s)
            return TvStoryboardGenerateOutput(
                shots=[
                    TvStoryboardShot(
                        shot_id=f"shot_{idx + 1}",
                        sequence=idx,
                        duration_s=parts[idx],
                        purpose=f"Shot purpose {idx + 1}",
                        visual_description=f"Storyboard shot {idx + 1} visual direction.",
                        camera_intent="handheld_follow" if idx == 0 else "hard_cut_progression",
                        transition_in="opening" if idx == 0 else "hard_cut",
                    )
                    for idx in range(4)
                ]
            )
        normalized = []
        for idx, shot in enumerate(existing[:8]):
            normalized.append(
                shot.model_copy(
                    update={
                        "shot_id": f"shot_{idx + 1}",
                        "sequence": idx,
                        "transition_in": "opening" if idx == 0 else "hard_cut",
                    }
                )
            )
        durations = [shot.duration_s for shot in normalized]
        balanced = self._rebalance_duration(durations, target_duration_s=target_duration_s)
        normalized = [
            shot.model_copy(update={"duration_s": balanced[idx]})
            for idx, shot in enumerate(normalized)
        ]
        return TvStoryboardGenerateOutput(shots=normalized)

    @staticmethod
    def _rebalance_duration(durations: list[int], *, target_duration_s: int) -> list[int]:
        if not durations:
            return [min(15, max(1, target_duration_s))]
        out = [min(15, max(1, int(v))) for v in durations]
        current = sum(out)
        guard = 0
        while current != target_duration_s and guard < 500:
            guard += 1
            if current < target_duration_s:
                changed = False
                for idx in range(len(out)):
                    if out[idx] < 15:
                        out[idx] += 1
                        current += 1
                        changed = True
                        if current == target_duration_s:
                            break
                if not changed:
                    out.append(1)
                    current += 1
            else:
                changed = False
                for idx in range(len(out)):
                    if out[idx] > 1:
                        out[idx] -= 1
                        current -= 1
                        changed = True
                        if current == target_duration_s:
                            break
                if not changed:
                    break
        return out


storyboard_service = StoryboardService()
