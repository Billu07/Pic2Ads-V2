import json
from typing import Literal, cast

import httpx

from app.agents.base import Agent
from app.clients.openai_client import openai_client
from app.models.scripts import (
    DialogueBeat,
    ScreenwriterInput,
    ScreenwriterOutput,
    ScriptVariant,
    VisualBeat,
)


class ScreenwriterAgent(Agent[ScreenwriterInput, ScreenwriterOutput]):
    name = "screenwriter"
    prompt_version = "openai-ugc-v1"

    async def run(self, payload: ScreenwriterInput) -> ScreenwriterOutput:
        try:
            generated = await openai_client.screenwriter_from_context(payload)
            return self._normalize_output(payload=payload, output=generated)
        except (RuntimeError, httpx.HTTPError, ValueError, json.JSONDecodeError):
            return self._heuristic_fallback(payload)

    def _normalize_output(
        self, *, payload: ScreenwriterInput, output: ScreenwriterOutput
    ) -> ScreenwriterOutput:
        if payload.mode == "pro_arc":
            if not output.scripts:
                return self._heuristic_fallback(payload)
            first = output.scripts[0]
            normalized = first.model_copy(
                update={
                    "variant_id": "pro_arc_master",
                    "render_pattern_hint": self._coerce_pro_arc_pattern(first.render_pattern_hint),
                    "segment_count_hint": None,
                }
            )
            return ScreenwriterOutput(mode=payload.mode, scripts=[normalized])

        if payload.mode == "tv":
            if not output.scripts:
                return self._heuristic_fallback(payload)
            first = output.scripts[0]
            shot_count = first.segment_count_hint if first.segment_count_hint else 4
            shot_count = max(3, min(8, int(shot_count)))
            normalized = first.model_copy(
                update={
                    "variant_id": "tv_master",
                    "render_pattern_hint": "tv_shotlist",
                    "segment_count_hint": shot_count,
                }
            )
            return ScreenwriterOutput(mode=payload.mode, scripts=[normalized])

        expected_ids = {
            "ugc_excited_discovery",
            "ugc_casual_recommendation",
            "ugc_in_the_moment_demo",
        }
        normalized: list[ScriptVariant] = []
        seen_ids: set[str] = set()
        for variant in output.scripts:
            vid = variant.variant_id.strip().lower().replace(" ", "_")
            if vid in expected_ids and vid not in seen_ids:
                normalized.append(variant.model_copy(update={"variant_id": vid}))
                seen_ids.add(vid)

        if len(normalized) == 3:
            return ScreenwriterOutput(mode=payload.mode, scripts=normalized)

        return self._heuristic_fallback(payload)

    @staticmethod
    def _coerce_pro_arc_pattern(
        pattern: str,
    ) -> Literal["single_take", "two_cuts", "three_cuts"]:
        if pattern in {"single_take", "two_cuts", "three_cuts"}:
            return cast(Literal["single_take", "two_cuts", "three_cuts"], pattern)
        return "single_take"

    @staticmethod
    def _heuristic_fallback(payload: ScreenwriterInput) -> ScreenwriterOutput:
        if payload.mode != "ugc":
            pattern_hint: Literal["single_take", "tv_shotlist"] = (
                "single_take" if payload.mode == "pro_arc" else "tv_shotlist"
            )
            segment_count_hint = 4 if payload.mode == "tv" else None
            return ScreenwriterOutput(
                mode=payload.mode,
                scripts=[
                    ScriptVariant(
                        variant_id="pro_arc_master" if payload.mode == "pro_arc" else "tv_master",
                        angle="single_narrative",
                        setting="everyday indoor environment with natural light",
                        tone="grounded and product-led",
                        filming_method="handheld product-forward shot",
                        first_frame_description=(
                            f"Close product-forward frame of {payload.product_name} in a real-use setting."
                        ),
                        product_feature_focus="core practical product benefit",
                        hook=f"Simple practical use-case for {payload.product_name}.",
                        render_pattern_hint=pattern_hint,
                        segment_count_hint=segment_count_hint,
                        dialogue_beats=[
                            DialogueBeat(
                                t_start=0.0,
                                t_end=float(min(5, payload.duration_s)),
                                line=f"I've been using {payload.product_name} and it fits my routine.",
                            )
                        ],
                        visual_beats=[
                            VisualBeat(
                                t_start=0.0,
                                t_end=float(min(5, payload.duration_s)),
                                action="Show real product handling in a natural context.",
                            )
                        ],
                        authenticity_markers=["casual cadence", "ambient room tone"],
                    )
                ],
            )

        product = payload.product_name
        return ScreenwriterOutput(
            mode="ugc",
            scripts=[
                ScriptVariant(
                    variant_id="ugc_excited_discovery",
                    angle="excited_discovery",
                    setting="bright kitchen counter in morning light",
                    tone="enthusiastic but natural",
                    filming_method="front_camera_selfie",
                    first_frame_description=f"Creator holds {product} close to camera with genuine surprise.",
                    product_feature_focus="immediate ease-of-use moment",
                    hook=f"I didn't expect {product} to be this easy to use.",
                    render_pattern_hint="single_gen",
                    dialogue_beats=[
                        DialogueBeat(t_start=0.0, t_end=3.5, line=f"Okay, I just tried {product}."),
                        DialogueBeat(t_start=3.5, t_end=7.0, line="It actually fits my mornings."),
                        DialogueBeat(t_start=7.0, t_end=10.0, line="This is staying in my routine."),
                    ],
                    visual_beats=[
                        VisualBeat(t_start=0.0, t_end=3.0, action="Bring product to foreground with slight shake."),
                        VisualBeat(t_start=3.0, t_end=7.0, action="Quick in-hand demo while speaking to camera."),
                        VisualBeat(t_start=7.0, t_end=10.0, action="Creator smiles and nods, keeps product visible."),
                    ],
                    authenticity_markers=["minor camera shake", "natural filler words"],
                ),
                ScriptVariant(
                    variant_id="ugc_casual_recommendation",
                    angle="casual_recommendation",
                    setting="desk setup in soft afternoon window light",
                    tone="calm recommendation",
                    filming_method="phone_propped_both_hands",
                    first_frame_description=f"Creator casually places {product} next to daily essentials.",
                    product_feature_focus="daily convenience and consistency",
                    hook="If you're busy, this one is low effort.",
                    render_pattern_hint="single_gen",
                    dialogue_beats=[
                        DialogueBeat(t_start=0.0, t_end=3.0, line="Quick rec if your days are packed."),
                        DialogueBeat(t_start=3.0, t_end=6.8, line=f"{product} is easy to keep consistent."),
                        DialogueBeat(t_start=6.8, t_end=10.0, line="No complicated routine, just works."),
                    ],
                    visual_beats=[
                        VisualBeat(t_start=0.0, t_end=3.0, action="Natural desk setup with creator entering frame."),
                        VisualBeat(t_start=3.0, t_end=6.8, action="Hold product upright and point to key detail."),
                        VisualBeat(t_start=6.8, t_end=10.0, action="Casual end beat with product centered."),
                    ],
                    authenticity_markers=["candid pacing", "unpolished room background"],
                ),
                ScriptVariant(
                    variant_id="ugc_in_the_moment_demo",
                    angle="in_the_moment_demo",
                    setting="bathroom mirror area with practical ambient light",
                    tone="live demo confidence",
                    filming_method="back_camera_mirror",
                    first_frame_description=f"Creator starts mid-action while using {product} in real time.",
                    product_feature_focus="demonstrable tactile product interaction",
                    hook="Let me show you exactly how I use this.",
                    render_pattern_hint="single_gen",
                    dialogue_beats=[
                        DialogueBeat(t_start=0.0, t_end=2.8, line="I'm doing this in real time."),
                        DialogueBeat(t_start=2.8, t_end=6.5, line=f"This is where {product} makes things easier."),
                        DialogueBeat(t_start=6.5, t_end=10.0, line="You can see the difference right away."),
                    ],
                    visual_beats=[
                        VisualBeat(t_start=0.0, t_end=2.8, action="Open with mid-action movement and product in hand."),
                        VisualBeat(t_start=2.8, t_end=6.5, action="Show one clear application/demo step."),
                        VisualBeat(t_start=6.5, t_end=10.0, action="End on creator reaction plus product close-up."),
                    ],
                    authenticity_markers=["ambient room noise", "micro facial expressions"],
                ),
            ],
        )


screenwriter_agent = ScreenwriterAgent()
