-- Segment-level render graph for multi-shot/multi-segment jobs.

create table if not exists public.render_unit (
  id bigserial primary key,
  job_id text not null references public.ad_job(id) on delete cascade,
  sequence integer not null check (sequence >= 0),
  pattern text not null check (pattern in ('single_gen', 'extend_chain', 'cut_chain')),
  duration_s integer not null check (duration_s > 0),
  created_at timestamptz not null default timezone('utc', now()),
  unique (job_id, sequence)
);

create index if not exists render_unit_job_created_idx
  on public.render_unit (job_id, created_at desc);

create table if not exists public.segment (
  id bigserial primary key,
  render_unit_id bigint not null references public.render_unit(id) on delete cascade,
  "order" integer not null check ("order" >= 0),
  duration_s integer not null check (duration_s between 1 and 15),
  prompt_seed text null,
  status text not null default 'queued' check (status in ('queued', 'running', 'completed', 'failed')),
  output_video_url text null,
  output_last_frame_url text null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (render_unit_id, "order")
);

create index if not exists segment_render_unit_created_idx
  on public.segment (render_unit_id, created_at desc);

drop trigger if exists trg_segment_set_updated_at on public.segment;
create trigger trg_segment_set_updated_at
before update on public.segment
for each row
execute function public.set_updated_at();

alter table public.provider_task
  add column if not exists segment_id bigint null references public.segment(id) on delete set null;

create index if not exists provider_task_segment_id_idx
  on public.provider_task (segment_id);

