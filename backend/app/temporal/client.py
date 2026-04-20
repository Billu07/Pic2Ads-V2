from temporalio.client import Client

from app.core.config import settings

_client: Client | None = None


async def get_temporal_client() -> Client:
    global _client

    if not settings.temporal_enabled:
        raise RuntimeError("Temporal is disabled. Set TEMPORAL_ENABLED=true to use workflow dispatch.")

    if _client is None:
        _client = await Client.connect(
            settings.temporal_address,
            namespace=settings.temporal_namespace,
        )
    return _client

