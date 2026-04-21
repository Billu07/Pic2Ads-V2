from app.models.prompting import CreativeDecisions, PromptPackSpec
from app.services.jobs import job_service


class PromptOrchestrationService:
    _PACKS: dict[str, PromptPackSpec] = {
        "ugc": PromptPackSpec(
            pack_id="ugc_core_v1",
            mode="ugc",
            script_directives=[
                "Open with a tactile product moment in first 2 seconds.",
                "Prioritize everyday conversational language over polished ad copy.",
                "Keep benefit claims grounded in visibly demonstrable behavior.",
            ],
            concept_directives=[],
            storyboard_directives=[],
        ),
        "pro_arc": PromptPackSpec(
            pack_id="pro_arc_arc_v1",
            mode="pro_arc",
            script_directives=[
                "Force a clear friction-to-relief mini arc with visible transformation.",
                "Keep story beats physically observable, not narrated as abstract outcomes.",
                "Use one emotionally honest beat before any direct product praise.",
            ],
            concept_directives=[],
            storyboard_directives=[],
        ),
        "tv": PromptPackSpec(
            pack_id="tv_campaign_v1",
            mode="tv",
            script_directives=[
                "Preserve a campaign-grade narrative spine with a strong opener and payoff.",
                "Avoid hype language; let product proof and mise-en-scene carry trust.",
                "Keep each segment seed specific enough for shot-level rendering.",
            ],
            concept_directives=[
                "Return three materially distinct campaign directions, not surface variants.",
                "Each concept must map to a unique audience persuasion angle.",
                "Write treatments as production-ready direction, not dialogue scripts.",
            ],
            storyboard_directives=[
                "Every shot must have one non-negotiable communication purpose.",
                "Build rhythm with visual contrast between adjacent shots.",
                "Maintain fidelity to selected concept arc and avoid off-brief embellishments.",
            ],
        ),
    }

    def _pack_for_mode(self, mode: str) -> PromptPackSpec:
        return self._PACKS.get(mode, self._PACKS["ugc"])

    def _format_stage_directives(self, directives: list[str]) -> list[str]:
        out: list[str] = []
        for directive in directives:
            text = directive.strip()
            if text:
                out.append(text[:220])
        return out

    def get_for_job(self, job_id: str) -> dict | None:
        context = job_service.get_creative_context(job_id)
        if context is None:
            return None
        mode = str(context["mode"])
        pack = self._pack_for_mode(mode)
        decisions = CreativeDecisions.model_validate(context["decisions"])
        return {
            "job_id": job_id,
            "mode": mode,
            "prompt_pack_id": str(context["prompt_pack_id"] or pack.pack_id),
            "language_code": str(context.get("language_code") or "en"),
            "language_name": str(context.get("language_name") or "English"),
            "creative_decisions": decisions,
            "script_directives": self._format_stage_directives(pack.script_directives),
            "concept_directives": self._format_stage_directives(pack.concept_directives),
            "storyboard_directives": self._format_stage_directives(pack.storyboard_directives),
        }


prompt_orchestration_service = PromptOrchestrationService()
