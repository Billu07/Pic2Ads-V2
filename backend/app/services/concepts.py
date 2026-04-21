import json

import httpx

from app.clients.openai_client import openai_client
from app.models.concepts import (
    TvConcept,
    TvConceptGenerateInput,
    TvConceptGenerateOutput,
    TvConceptGenerateResponse,
    TvConceptListResponse,
)
from app.services.brand_strategy import brand_strategy_service
from app.services.casting import casting_service
from app.services.jobs import job_service
from app.services.prompt_orchestration import prompt_orchestration_service
from app.services.product_intel import product_intel_service


class ConceptService:
    async def generate_for_job(self, job_id: str) -> TvConceptGenerateResponse | None:
        job = job_service.get_job(job_id)
        if job is None:
            return None
        if job.mode != "tv":
            raise RuntimeError("concept_generation_only_for_tv_mode")

        cached = job_service.get_tv_concepts(job_id)
        if cached is None:
            return None
        if cached:
            validated = [TvConcept.model_validate(item) for item in cached]
            return TvConceptGenerateResponse(job_id=job_id, cached=True, concepts=validated)

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

        context = job_service.get_job_product_context(job_id)
        if context is None:
            return None
        product_name, _ = context

        prompt_context = prompt_orchestration_service.get_for_job(job_id)
        if prompt_context is None:
            return None

        payload = TvConceptGenerateInput(
            language_code=str(prompt_context.get("language_code") or "en"),
            language_name=str(prompt_context.get("language_name") or "English"),
            product_name=product_name,
            brief=self._read_job_brief(job_id),
            duration_s=job.duration_s,
            prompt_pack_id=str(prompt_context["prompt_pack_id"]),
            prompt_directives=list(prompt_context["concept_directives"]),
            creative_decisions=prompt_context["creative_decisions"],
            product_intel=intel_run.output,
            brand_constraints=brand_run.output,
            persona=casting_run.output,
        )

        try:
            generated = await openai_client.tv_concepts_from_context(payload)
            normalized = self._normalize_generated(generated)
        except (RuntimeError, httpx.HTTPError, ValueError, json.JSONDecodeError):
            normalized = self._heuristic_fallback(payload)

        dumped = [item.model_dump() for item in normalized.concepts]
        saved = job_service.set_tv_concepts(job_id, dumped)
        if not saved:
            return None
        return TvConceptGenerateResponse(job_id=job_id, cached=False, concepts=normalized.concepts)

    def list_for_job(self, job_id: str) -> TvConceptListResponse | None:
        concepts = job_service.get_tv_concepts(job_id)
        if concepts is None:
            return None
        validated = [TvConcept.model_validate(item) for item in concepts]
        return TvConceptListResponse(
            job_id=job_id,
            generated=bool(validated),
            concepts=validated,
        )

    @staticmethod
    def _read_job_brief(job_id: str) -> str | None:
        # Reuse workflow_state and product context in services; brief comes from ad_job directly.
        from app.db.client import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select brief from public.ad_job where id = %s", (job_id,))
                row = cur.fetchone()
        if row is None or row["brief"] is None:
            return None
        return str(row["brief"])

    def _normalize_generated(self, output: TvConceptGenerateOutput) -> TvConceptGenerateOutput:
        target_ids = ["concept_1", "concept_2", "concept_3"]
        concepts = output.concepts[:3]
        if len(concepts) < 3:
            return self._heuristic_fallback_from_existing(concepts)
        normalized: list[TvConcept] = []
        for idx, concept in enumerate(concepts):
            normalized.append(concept.model_copy(update={"concept_id": target_ids[idx]}))
        return TvConceptGenerateOutput(concepts=normalized)

    def _heuristic_fallback(self, payload: TvConceptGenerateInput) -> TvConceptGenerateOutput:
        tone = ", ".join(payload.brand_constraints.tone_descriptors[:3]) or "credible, modern"
        product = payload.product_name
        persona_name = payload.persona.name
        concepts = [
            TvConcept(
                concept_id="concept_1",
                title="Problem-to-Relief Arc",
                logline=f"{persona_name} moves from daily friction to smooth routine using {product}.",
                treatment=(
                    "Open on a relatable daily pain point, then transition into a grounded product-use moment. "
                    "Show one practical interaction and end with a calm confidence beat that feels earned."
                ),
                audience_angle="Busy professionals who value predictable routines.",
                style_notes=[tone, "natural light realism", "product-forward hero beat"],
            ),
            TvConcept(
                concept_id="concept_2",
                title="Social Proof in Motion",
                logline=f"Peer-to-peer confidence framing where {product} is endorsed through lived routine.",
                treatment=(
                    "Start with an in-context lifestyle setup, then deliver concise testimony with physical product "
                    "interaction. Reinforce trust through specific use moments, not claims-heavy narration."
                ),
                audience_angle="Skeptical viewers seeking proof before trial.",
                style_notes=[tone, "camera intimacy", "authentic micro-imperfections"],
            ),
            TvConcept(
                concept_id="concept_3",
                title="Feature-as-Story Device",
                logline=f"A single standout feature of {product} becomes the narrative hinge of the ad.",
                treatment=(
                    "Frame one product feature as the unlock in a short emotional arc. Build visual rhythm across "
                    "3-5 planned shots, ending with a composed hero frame and quiet CTA-ready finish."
                ),
                audience_angle="Performance-focused buyers who compare alternatives.",
                style_notes=[tone, "clean composition", "paced editorial cuts"],
            ),
        ]
        return TvConceptGenerateOutput(concepts=concepts)

    def _heuristic_fallback_from_existing(self, existing: list[TvConcept]) -> TvConceptGenerateOutput:
        seed = existing[0] if existing else TvConcept(
            concept_id="concept_1",
            title="Core Concept",
            logline="Core logline",
            treatment="Core treatment",
            audience_angle="Core audience",
            style_notes=["grounded", "credible"],
        )
        concepts = []
        for idx, cid in enumerate(["concept_1", "concept_2", "concept_3"]):
            if idx < len(existing):
                concepts.append(existing[idx].model_copy(update={"concept_id": cid}))
            else:
                concepts.append(
                    seed.model_copy(
                        update={
                            "concept_id": cid,
                            "title": f"{seed.title} Variant {idx + 1}",
                        }
                    )
                )
        return TvConceptGenerateOutput(concepts=concepts)


concept_service = ConceptService()
