from datetime import timedelta

from temporalio import workflow

from app.models.workflows import GenerateAdInput, GenerateAdResult, RenderUnitInput, RenderUnitResult


@workflow.defn
class GenerateAdWorkflow:
    @workflow.run
    async def run(self, payload: GenerateAdInput) -> GenerateAdResult:
        await workflow.execute_activity(
            "product_intel_activity",
            payload.job_id,
            schedule_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            "duration_plan_activity",
            payload.job_id,
            schedule_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            "video_generate_activity",
            payload.job_id,
            schedule_to_close_timeout=timedelta(seconds=30),
        )
        return GenerateAdResult(
            job_id=payload.job_id,
            status="queued_to_temporal",
            message=f"GenerateAdWorkflow accepted for mode={payload.mode}",
        )


@workflow.defn
class RenderUnitWorkflow:
    @workflow.run
    async def run(self, payload: RenderUnitInput) -> RenderUnitResult:
        await workflow.execute_activity(
            "video_generate_activity",
            payload.job_id,
            schedule_to_close_timeout=timedelta(seconds=30),
        )
        return RenderUnitResult(
            job_id=payload.job_id,
            unit_sequence=payload.unit_sequence,
            status="queued_to_temporal",
        )

