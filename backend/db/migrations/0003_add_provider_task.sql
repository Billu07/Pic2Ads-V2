-- Provider task mapping for webhook/status correlation.

create table if not exists public.provider_task (
  id bigserial primary key,
  job_id text not null references public.ad_job(id) on delete cascade,
  provider text not null,
  provider_task_id text not null,
  model text null,
  status text not null default 'submitted',
  submit_payload jsonb not null default '{}'::jsonb,
  latest_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists provider_task_provider_task_id_uidx
  on public.provider_task (provider, provider_task_id);

create index if not exists provider_task_job_created_idx
  on public.provider_task (job_id, created_at desc);

drop trigger if exists trg_provider_task_set_updated_at on public.provider_task;
create trigger trg_provider_task_set_updated_at
before update on public.provider_task
for each row
execute function public.set_updated_at();

