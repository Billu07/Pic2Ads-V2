import hashlib
import json
import time

from psycopg.types.json import Json

from app.agents.screenwriter import screenwriter_agent
from app.db.client import get_db_connection
from app.models.creative import BrandConstraintsOutput, PersonaOutput
from app.models.product_intel import ProductIntelOutput
from app.models.scripts import ScreenwriterInput, ScreenwriterOutput, ScriptRunResponse
from app.services.brand_strategy import brand_strategy_service
from app.services.casting import casting_service
from app.services.prompt_orchestration import prompt_orchestration_service
from app.services.product_intel import product_intel_service


class ScriptService:
    def __init__(self) -> None:
        self.agent = screenwriter_agent

    @staticmethod
    def _input_hash(payload: ScreenwriterInput) -> str:
        canonical = json.dumps(payload.model_dump(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    async def run_for_job(
        self,
        job_id: str,
        *,
        product_intel: ProductIntelOutput | None = None,
        brand_constraints: BrandConstraintsOutput | None = None,
        persona: PersonaOutput | None = None,
    ) -> ScriptRunResponse | None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select mode::text as mode, duration_s, product_name, product_image_url, brief
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

        cast = persona
        if cast is None:
            cast_run = await casting_service.run_for_job(
                job_id,
                product_intel=intel,
                brand_constraints=brand,
            )
            if cast_run is None:
                return None
            cast = cast_run.output

        prompt_context = prompt_orchestration_service.get_for_job(job_id)
        if prompt_context is None:
            return None

        payload = ScreenwriterInput(
            mode=str(job_row["mode"]),
            language_code=str(prompt_context.get("language_code") or "en"),
            language_name=str(prompt_context.get("language_name") or "English"),
            duration_s=int(job_row["duration_s"]),
            product_name=str(job_row["product_name"]),
            product_image_url=str(job_row["product_image_url"]),
            brief=str(job_row["brief"]) if job_row["brief"] else None,
            prompt_pack_id=str(prompt_context["prompt_pack_id"]),
            prompt_directives=list(prompt_context["script_directives"]),
            creative_decisions=prompt_context["creative_decisions"],
            product_intel=intel,
            brand_constraints=brand,
            persona=cast,
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
            cached_output = ScreenwriterOutput.model_validate(cached_row["output"])
            return ScriptRunResponse(
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

        return ScriptRunResponse(
            job_id=job_id,
            cached=False,
            agent_name=self.agent.name,
            prompt_version=self.agent.prompt_version,
            output=output,
        )

    def get_cached_for_job(self, job_id: str) -> ScriptRunResponse | None:
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
        cached_output = ScreenwriterOutput.model_validate(row["output"])
        return ScriptRunResponse(
            job_id=job_id,
            cached=True,
            agent_name=self.agent.name,
            prompt_version=str(row["prompt_version"]),
            output=cached_output,
        )


script_service = ScriptService()
