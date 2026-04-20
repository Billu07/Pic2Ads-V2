# Pic2Ads Backend (Step 1)

This is the first implementation step for Pic2Ads.

## What exists now
- FastAPI service skeleton
- Settings loader using environment variables
- Basic `jobs` API surface (create + status) backed by Postgres
- Local orchestrator endpoint: `POST /v1/jobs/{job_id}/pipeline/run-local`
- Product Intelligence endpoint (`POST /v1/jobs/{job_id}/intel`) with GPT-4o vision call + DB persistence
- Brand strategy endpoint (`POST /v1/jobs/{job_id}/brand-strategy`) for mode-aware tone/claims constraints
- Casting endpoint (`POST /v1/jobs/{job_id}/casting`) for creator persona generation
- Screenwriter endpoint (`POST /v1/jobs/{job_id}/scripts`) with mode-aware script generation + cache replay
- TV gate endpoints:
  - `GET /v1/jobs/{job_id}/tv/gates`
  - `POST /v1/jobs/{job_id}/concepts/select`
  - `POST /v1/jobs/{job_id}/storyboard/approve`
- Seedance submit endpoint (`POST /v1/jobs/{job_id}/seedance/submit`) storing `taskId` mappings (supports `Idempotency-Key`)
- Render graph endpoints:
  - `POST /v1/jobs/{job_id}/units` (create render unit + segments)
  - `GET /v1/jobs/{job_id}/units` (list units + segment state)
- Agent base interfaces and shared typed models
- SQL migration runner for Supabase/Postgres
- Temporal workflow/worker skeleton (optional, env-gated)
- Seedance callback skeleton (`POST /v1/webhooks/kie`) with taskId-based status correlation
- Seedance polling sync endpoint (`POST /v1/jobs/{job_id}/seedance/tasks/{task_id}/sync`)
- Seedance retry runner endpoint (`POST /v1/jobs/seedance/retries/run`) to process due retries
- Export manifest endpoint (`GET /v1/jobs/{job_id}/export/manifest`) for editor/export timeline
- Provider task records now persist extracted output URLs + metadata from callback/sync payloads
- Segment rows are linked to provider tasks and receive status/output updates on sync/webhook
- Failed provider tasks now use retry scheduling and dead-letter fallback
- Due retries are now claimable/resubmittable from `next_retry_at` with stale-task callback protection
- Segment regen endpoint: `POST /v1/jobs/{job_id}/segments/{segment_id}/regen`
- `run-local` now runs: Product Intel -> Brand Strategist -> Casting Director -> Screenwriter -> Duration Planner -> Seedance submit
- For `mode=tv`, `run-local` blocks render submission until concept is selected and storyboard is approved.

## Run locally
1. `cd backend`
2. Create venv and install deps
3. Set `DATABASE_URL` (or `SUPABASE_DB_URL`) in `.env`
4. Run migrations: `python -m app.db.migrate`
5. `uvicorn app.main:app --reload --port 8000`

## Optional Temporal (Step 2)
Note: `temporalio` currently targets Python 3.11/3.12 in practice. If your system Python is newer (for example 3.14), run worker/API in a 3.11/3.12 virtualenv.

1. Set:
   - `TEMPORAL_ENABLED=true`
   - `TEMPORAL_ADDRESS=<your-temporal-host:7233>`
   - `TEMPORAL_NAMESPACE=default` (or your namespace)
   - `TEMPORAL_TASK_QUEUE=pic2ads-main`
2. Run worker: `python -m app.temporal.worker`
3. Dispatch a job after creation: `POST /v1/jobs/{job_id}/dispatch`

## Environment
Copy `.env.example` to `.env` and adjust values.
`KIE_CALLBACK_URL` must point to this backend service (for example `https://api.pic2ads.io/v1/webhooks/kie`), not a frontend-only host.

Retry worker knobs:
- `KIE_RETRY_WORKER_ENABLED=true` to run a retry loop inside API process
- `KIE_RETRY_WORKER_INTERVAL_SECONDS=20`
- `KIE_RETRY_WORKER_BATCH_SIZE=10`

Run standalone retry worker process:
- `python -m app.workers.seedance_retry_worker`

## Next build steps
1. Add signed webhook verification once Kie signature format is finalized
2. Add segment-level QA checks and automatic regen triggers
3. Add editor/export pipeline consuming segment `output_video_url` fields
