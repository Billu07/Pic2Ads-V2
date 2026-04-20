import hashlib
import json
import time

from psycopg.types.json import Json

from app.agents.product_intel import ProductIntelAgent
from app.db.client import get_db_connection
from app.models.product_intel import ProductIntelInput, ProductIntelOutput, ProductIntelRunResponse


class ProductIntelService:
    def __init__(self) -> None:
        self.agent = ProductIntelAgent()

    @staticmethod
    def _input_hash(payload: ProductIntelInput) -> str:
        canonical = json.dumps(payload.model_dump(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    async def run_for_job(self, job_id: str) -> ProductIntelRunResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select product_name, product_image_url
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                job_row = cur.fetchone()

        if job_row is None:
            return None

        payload = ProductIntelInput(
            product_name=str(job_row["product_name"]),
            product_image_url=str(job_row["product_image_url"]),
        )
        input_hash = self._input_hash(payload)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select output
                    from public.agent_output
                    where job_id = %s
                      and agent_name = %s
                      and input_hash = %s
                    order by created_at desc
                    limit 1
                    """,
                    (job_id, self.agent.name, input_hash),
                )
                cached_row = cur.fetchone()

        if cached_row is not None:
            cached_output = ProductIntelOutput.model_validate(cached_row["output"])
            return ProductIntelRunResponse(
                job_id=job_id,
                cached=True,
                agent_name=self.agent.name,
                prompt_version=self.agent.prompt_version,
                output=cached_output,
            )

        started = time.perf_counter()
        output = await self.agent.run(payload)
        latency_ms = int((time.perf_counter() - started) * 1000)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into public.agent_output (
                      job_id,
                      agent_name,
                      prompt_version,
                      input_hash,
                      output,
                      tokens_in,
                      tokens_out,
                      cost_usd,
                      latency_ms
                    ) values (%s, %s, %s, %s, %s, 0, 0, 0, %s)
                    on conflict (job_id, agent_name, input_hash) do nothing
                    """,
                    (
                        job_id,
                        self.agent.name,
                        self.agent.prompt_version,
                        input_hash,
                        Json(output.model_dump()),
                        latency_ms,
                    ),
                )
            conn.commit()

        return ProductIntelRunResponse(
            job_id=job_id,
            cached=False,
            agent_name=self.agent.name,
            prompt_version=self.agent.prompt_version,
            output=output,
        )


product_intel_service = ProductIntelService()

