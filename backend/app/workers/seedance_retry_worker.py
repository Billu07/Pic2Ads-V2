import asyncio

from app.core.config import settings
from app.services.seedance_retry_worker import seedance_retry_worker_service


async def run_worker() -> None:
    await seedance_retry_worker_service.run_forever(
        poll_interval_seconds=settings.fal_retry_worker_interval_seconds,
        batch_size=settings.fal_retry_worker_batch_size,
    )


if __name__ == "__main__":
    asyncio.run(run_worker())
