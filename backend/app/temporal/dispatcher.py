from app.core.config import settings
from app.models.workflows import GenerateAdInput
from app.temporal.client import get_temporal_client
from app.workflows.pipeline import GenerateAdWorkflow


async def dispatch_generate_ad(job_id: str, mode: str) -> str:
    client = await get_temporal_client()
    workflow_id = f"generate-ad-{job_id}"
    handle = await client.start_workflow(
        GenerateAdWorkflow.run,
        GenerateAdInput(job_id=job_id, mode=mode),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    return handle.id

