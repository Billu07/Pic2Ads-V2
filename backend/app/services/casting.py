import hashlib
import json
import time

from psycopg.types.json import Json

from app.agents.casting_director import casting_director_agent
from app.db.client import get_db_connection
from app.models.creative import (
    BrandConstraintsOutput,
    CastingInput,
    CastingRunResponse,
    PersonaOutput,
)
from app.models.product_intel import ProductIntelOutput
from app.services.brand_strategy import brand_strategy_service
from app.services.product_intel import product_intel_service


class CastingService:
    def __init__(self) -> None:
        self.agent = casting_director_agent

    @staticmethod
    def _input_hash(payload: CastingInput) -> str:
        canonical = json.dumps(payload.model_dump(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    async def run_for_job(
        self,
        job_id: str,
        *,
        product_intel: ProductIntelOutput | None = None,
        brand_constraints: BrandConstraintsOutput | None = None,
    ) -> CastingRunResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select mode::text as mode, product_name, product_image_url, brief
                    from public.ad_job
                    where id = %s
                    """,
                    (job_id,),
                )
                job_row = cur.fetchone()
        if job_row is None:
            return None

        intel = product_intel
        if intel is None:
            intel_run = await product_intel_service.run_for_job(job_id)
            if intel_run is None:
                return None
            intel = intel_run.output

        brand = brand_constraints
        if brand is None:
            brand_run = await brand_strategy_service.run_for_job(job_id, product_intel=intel)
            if brand_run is None:
                return None
            brand = brand_run.output

        payload = CastingInput(
            mode=str(job_row["mode"]),
            product_name=str(job_row["product_name"]),
            brief=str(job_row["brief"]) if job_row["brief"] else None,
            product_image_url=str(job_row["product_image_url"]),
            product_intel=intel,
            brand_constraints=brand,
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
            return CastingRunResponse(
                job_id=job_id,
                cached=True,
                agent_name=self.agent.name,
                prompt_version=self.agent.prompt_version,
                output=PersonaOutput.model_validate(cached_row["output"]),
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

        return CastingRunResponse(
            job_id=job_id,
            cached=False,
            agent_name=self.agent.name,
            prompt_version=self.agent.prompt_version,
            output=output,
        )

    def get_cached_for_job(self, job_id: str) -> CastingRunResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select output, prompt_version
                    from public.agent_output
                    where job_id = %s
                      and agent_name = %s
                    order by created_at desc
                    limit 1
                    """,
                    (job_id, self.agent.name),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return CastingRunResponse(
            job_id=job_id,
            cached=True,
            agent_name=self.agent.name,
            prompt_version=str(row["prompt_version"]),
            output=PersonaOutput.model_validate(row["output"]),
        )


casting_service = CastingService()

