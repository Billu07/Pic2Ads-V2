import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.services.seedance_retry_worker import seedance_retry_worker_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    retry_task: asyncio.Task[None] | None = None
    if settings.fal_retry_worker_enabled:
        retry_task = asyncio.create_task(
            seedance_retry_worker_service.run_forever(
                poll_interval_seconds=settings.fal_retry_worker_interval_seconds,
                batch_size=settings.fal_retry_worker_batch_size,
            )
        )
    try:
        yield
    finally:
        if retry_task is not None:
            retry_task.cancel()
            with suppress(asyncio.CancelledError):
                await retry_task


app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)
app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "env": settings.app_env}
