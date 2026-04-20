import asyncio

from temporalio.worker import Worker

from app.activities.pipeline import (
    duration_plan_activity,
    product_intel_activity,
    video_generate_activity,
)
from app.core.config import settings
from app.temporal.client import get_temporal_client
from app.workflows.pipeline import GenerateAdWorkflow, RenderUnitWorkflow


async def run_worker() -> None:
    client = await get_temporal_client()
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[GenerateAdWorkflow, RenderUnitWorkflow],
        activities=[product_intel_activity, duration_plan_activity, video_generate_activity],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())

