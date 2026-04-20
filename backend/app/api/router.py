from fastapi import APIRouter

from app.api.routes.exports import router as exports_router
from app.api.routes.health import router as health_router
from app.api.routes.intel import router as intel_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.render import router as render_router
from app.api.routes.seedance import router as seedance_router
from app.api.routes.webhooks import router as webhooks_router
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(health_router, tags=["health"])
api_router.include_router(jobs_router, tags=["jobs"])
api_router.include_router(intel_router, tags=["intel"])
api_router.include_router(render_router, tags=["render"])
api_router.include_router(seedance_router, tags=["seedance"])
api_router.include_router(webhooks_router, tags=["webhooks"])
api_router.include_router(exports_router, tags=["exports"])
