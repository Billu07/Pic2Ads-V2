from app.models.render import RenderUnitCreateRequest, SegmentCreateRequest
from app.models.scripts import ScriptVariant
from app.services.jobs import job_service
from app.services.render_units import render_unit_service
from app.services.scripts import script_service


class DurationPlannerService:
    async def ensure_units_for_job(self, job_id: str) -> int:
        existing = render_unit_service.list_units(job_id).units
        if existing:
            return len(existing)

        job = job_service.get_job(job_id)
        if job is None:
            raise RuntimeError("job_not_found")
        language_code = job_service.get_language_code(job_id)

        scripts_run = script_service.get_cached_for_job(job_id)
        if scripts_run is None:
            scripts_run = await script_service.run_for_job(job_id)
        if scripts_run is None:
            raise RuntimeError("job_not_found")

        if job.mode == "ugc":
            return self._build_ugc_units(
                job_id=job_id,
                duration_s=int(job.duration_s),
                scripts=scripts_run.output.scripts,
                language_code=language_code,
            )
        if job.mode == "pro_arc":
            return self._build_pro_arc_unit(
                job_id=job_id,
                duration_s=int(job.duration_s),
                scripts=scripts_run.output.scripts,
                language_code=language_code,
            )
        return self._build_tv_unit(
            job_id=job_id,
            duration_s=int(job.duration_s),
            scripts=scripts_run.output.scripts,
            language_code=language_code,
        )

    @staticmethod
    def _split_segments(duration_s: int) -> list[int]:
        segments: list[int] = []
        remaining = max(1, duration_s)
        while remaining > 0:
            seg_dur = min(15, remaining)
            segments.append(seg_dur)
            remaining -= seg_dur
        return segments

    def _build_ugc_units(
        self,
        *,
        job_id: str,
        duration_s: int,
        scripts: list[ScriptVariant],
        language_code: str,
    ) -> int:
        total_units = 0
        duration_parts = self._split_segments(duration_s)
        for sequence, script in enumerate(scripts):
            pattern = "single_gen" if len(duration_parts) == 1 else "extend_chain"
            segments = [
                SegmentCreateRequest(
                    order=idx,
                    duration_s=seg_dur,
                    prompt_seed=self._ugc_prompt_seed(
                        script=script,
                        language_code=language_code,
                        segment_index=idx,
                        total_segments=len(duration_parts),
                        segment_duration_s=seg_dur,
                    ),
                )
                for idx, seg_dur in enumerate(duration_parts)
            ]
            created = render_unit_service.create_unit(
                job_id,
                RenderUnitCreateRequest(
                    sequence=sequence,
                    pattern=pattern,
                    duration_s=duration_s,
                    segments=segments,
                ),
            )
            if created is None:
                raise RuntimeError("job_not_found")
            total_units += 1
        return total_units

    def _build_pro_arc_unit(
        self,
        *,
        job_id: str,
        duration_s: int,
        scripts: list[ScriptVariant],
        language_code: str,
    ) -> int:
        primary_script = scripts[0] if scripts else None
        pattern_hint = primary_script.render_pattern_hint if primary_script else "single_take"
        if pattern_hint not in {"single_take", "two_cuts", "three_cuts"}:
            pattern_hint = "single_take"

        if pattern_hint == "single_take":
            duration_parts = self._split_segments(duration_s)
            pattern = "single_gen" if len(duration_parts) == 1 else "extend_chain"
        else:
            segment_count = 2 if pattern_hint == "two_cuts" else 3
            duration_parts = self._split_duration_by_count(duration_s, segment_count=segment_count)
            pattern = "cut_chain"

        segments = [
            SegmentCreateRequest(
                order=idx,
                duration_s=seg_dur,
                prompt_seed=self._non_ugc_prompt_seed(
                    mode="pro_arc",
                    script=primary_script,
                    language_code=language_code,
                    segment_index=idx,
                    total_segments=len(duration_parts),
                    segment_duration_s=seg_dur,
                    pattern_hint=pattern_hint,
                ),
            )
            for idx, seg_dur in enumerate(duration_parts)
        ]

        created = render_unit_service.create_unit(
            job_id,
            RenderUnitCreateRequest(
                sequence=0,
                pattern=pattern,
                duration_s=duration_s,
                segments=segments,
            ),
        )
        if created is None:
            raise RuntimeError("job_not_found")
        return 1

    def _build_tv_unit(
        self,
        *,
        job_id: str,
        duration_s: int,
        scripts: list[ScriptVariant],
        language_code: str,
    ) -> int:
        primary_script = scripts[0] if scripts else None
        storyboard = job_service.get_tv_storyboard(job_id)

        duration_parts: list[int]
        shot_notes: list[str]
        if storyboard and isinstance(storyboard.get("shots"), list) and len(storyboard["shots"]) > 0:
            duration_parts = []
            shot_notes = []
            for shot in storyboard["shots"]:
                if not isinstance(shot, dict):
                    continue
                raw_duration = shot.get("duration_s")
                duration = int(raw_duration) if isinstance(raw_duration, int | float) else 5
                duration = max(1, duration)
                purpose = str(shot.get("purpose") or "")
                visual = str(shot.get("visual_description") or "")
                note = f"purpose={purpose}; visual={visual}"[:260]
                while duration > 15:
                    duration_parts.append(15)
                    shot_notes.append(f"{note}; split_part=15")
                    duration -= 15
                duration_parts.append(duration)
                shot_notes.append(note)
            if not duration_parts:
                duration_parts = self._split_segments(duration_s)
                shot_notes = ["" for _ in duration_parts]
            duration_parts = self._rebalance_to_total(duration_parts, target_total=duration_s)
            if len(shot_notes) < len(duration_parts):
                shot_notes.extend([""] * (len(duration_parts) - len(shot_notes)))
            elif len(shot_notes) > len(duration_parts):
                shot_notes = shot_notes[: len(duration_parts)]
        else:
            desired = primary_script.segment_count_hint if primary_script and primary_script.segment_count_hint else 4
            segment_count = max(3, min(8, int(desired)))
            duration_parts = self._split_duration_by_count(duration_s, segment_count=segment_count)
            shot_notes = ["" for _ in duration_parts]

        segments = []
        for idx, seg_dur in enumerate(duration_parts):
            prompt = self._non_ugc_prompt_seed(
                mode="tv",
                script=primary_script,
                language_code=language_code,
                segment_index=idx,
                total_segments=len(duration_parts),
                segment_duration_s=seg_dur,
                pattern_hint="tv_shotlist",
            )
            note = shot_notes[idx] if idx < len(shot_notes) else ""
            if note:
                prompt = f"{prompt} Storyboard shot note: {note}"[:1900]
            segments.append(
                SegmentCreateRequest(
                    order=idx,
                    duration_s=seg_dur,
                    prompt_seed=prompt,
                )
            )

        created = render_unit_service.create_unit(
            job_id,
            RenderUnitCreateRequest(
                sequence=0,
                pattern="cut_chain",
                duration_s=duration_s,
                segments=segments,
            ),
        )
        if created is None:
            raise RuntimeError("job_not_found")
        return 1

    def _split_duration_by_count(self, duration_s: int, *, segment_count: int) -> list[int]:
        if segment_count <= 1:
            return self._split_segments(duration_s)
        base = duration_s // segment_count
        rem = duration_s % segment_count
        parts: list[int] = []
        for idx in range(segment_count):
            value = base + (1 if idx < rem else 0)
            parts.append(max(1, value))

        # Normalize to max 15s by splitting offending segments.
        normalized: list[int] = []
        for value in parts:
            while value > 15:
                normalized.append(15)
                value -= 15
            normalized.append(value)
        # Rebalance if normalization increased total parts unexpectedly.
        return self._rebalance_to_total(normalized, target_total=duration_s)

    @staticmethod
    def _rebalance_to_total(parts: list[int], *, target_total: int) -> list[int]:
        if not parts:
            return [min(15, max(1, target_total))]
        out = [max(1, min(15, int(value))) for value in parts]
        current = sum(out)
        guard = 0
        while current != target_total and guard < 500:
            guard += 1
            if current < target_total:
                changed = False
                for idx in range(len(out)):
                    if out[idx] < 15:
                        out[idx] += 1
                        current += 1
                        changed = True
                        if current == target_total:
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
                        if current == target_total:
                            break
                if not changed:
                    break
        return out

    def _ugc_prompt_seed(
        self,
        *,
        script: ScriptVariant,
        language_code: str,
        segment_index: int,
        total_segments: int,
        segment_duration_s: int,
    ) -> str:
        dialogue = " ".join(beat.line.strip() for beat in script.dialogue_beats if beat.line.strip())
        visuals = " ".join(
            beat.action.strip() for beat in script.visual_beats if beat.action.strip()
        )
        authenticity = ", ".join(marker.strip() for marker in script.authenticity_markers if marker.strip())
        prompt = (
            f"UGC variant={script.variant_id}; angle={script.angle}; "
            f"segment={segment_index + 1}/{total_segments}; duration_s={segment_duration_s}. "
            f"Setting: {script.setting}. Tone: {script.tone}. Filming method: {script.filming_method}. "
            f"Hook: {script.hook}. Feature focus: {script.product_feature_focus}. "
            f"First frame: {script.first_frame_description}. Dialogue: {dialogue}. "
            f"Visual beats: {visuals}. Authenticity markers: {authenticity}. "
            f"Dialogue language requirement: {language_code}. "
            "Constraints: selfie-style realism; natural handheld motion; "
            "product appearance unchanged from source image; no visible phone, no subtitles, "
            "no overlays, no watermarks, no logo overlays."
        )
        return prompt[:1900]

    def _non_ugc_prompt_seed(
        self,
        *,
        mode: str,
        script: ScriptVariant | None,
        language_code: str,
        segment_index: int,
        total_segments: int,
        segment_duration_s: int,
        pattern_hint: str,
    ) -> str:
        if script is None:
            return (
                f"{mode} segment {segment_index + 1}/{total_segments}; duration_s={segment_duration_s}; "
                f"dialogue language requirement={language_code}; "
                "product fidelity locked; realistic camera behavior; no overlays."
            )[:1900]

        dialogue = " ".join(beat.line.strip() for beat in script.dialogue_beats if beat.line.strip())
        visuals = " ".join(beat.action.strip() for beat in script.visual_beats if beat.action.strip())
        authenticity = ", ".join(marker.strip() for marker in script.authenticity_markers if marker.strip())
        prompt = (
            f"{mode} segment {segment_index + 1}/{total_segments}; duration_s={segment_duration_s}; "
            f"pattern_hint={pattern_hint}; angle={script.angle}. "
            f"Setting: {script.setting}. Tone: {script.tone}. Filming method: {script.filming_method}. "
            f"Hook: {script.hook}. Feature focus: {script.product_feature_focus}. "
            f"First frame: {script.first_frame_description}. Dialogue: {dialogue}. "
            f"Visual beats: {visuals}. Authenticity markers: {authenticity}. "
            f"Dialogue language requirement: {language_code}. "
            "Constraints: product appearance unchanged from source image; no visible phone; no subtitles; "
            "no overlays; no watermarks."
        )
        return prompt[:1900]


duration_planner_service = DurationPlannerService()
