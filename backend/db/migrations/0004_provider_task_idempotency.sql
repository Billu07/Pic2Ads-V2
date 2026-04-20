alter table public.provider_task
  add column if not exists idempotency_key text null;

alter table public.provider_task
  add column if not exists submit_hash text null;

create unique index if not exists provider_task_job_provider_idempotency_uidx
  on public.provider_task (job_id, provider, idempotency_key)
  where idempotency_key is not null;

create unique index if not exists provider_task_job_provider_submit_hash_uidx
  on public.provider_task (job_id, provider, submit_hash)
  where submit_hash is not null;

