alter table public.provider_task
  add column if not exists retry_count integer not null default 0;

alter table public.provider_task
  add column if not exists next_retry_at timestamptz null;

alter table public.provider_task
  add column if not exists last_error_at timestamptz null;

alter table public.provider_task
  add column if not exists dead_lettered boolean not null default false;

create index if not exists provider_task_retry_due_idx
  on public.provider_task (provider, dead_lettered, next_retry_at)
  where dead_lettered = false and next_retry_at is not null;

