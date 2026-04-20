alter table public.provider_task
  add column if not exists output_video_url text null;

alter table public.provider_task
  add column if not exists output_last_frame_url text null;

alter table public.provider_task
  add column if not exists output_metadata jsonb not null default '{}'::jsonb;

alter table public.provider_task
  add column if not exists error_message text null;

alter table public.provider_task
  add column if not exists completed_at timestamptz null;

create index if not exists provider_task_job_status_idx
  on public.provider_task (job_id, status, created_at desc);

